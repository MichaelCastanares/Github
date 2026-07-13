"""Audio Metrics — measure SNR and Word Error Rate from a read passage.

The user reads a displayed passage aloud (~60s). The app records the audio,
estimates signal-to-noise ratio with a simple energy-based method, transcribes
the speech with faster-whisper, scores Word Error Rate against the reference
passage, and logs the session to SQLite.
"""

import io
import os
import csv
import json
import re
import hmac
import base64
import sqlite3
import hashlib
import zipfile
from html import escape as html_escape
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf
import streamlit as st
import streamlit.components.v1 as components

# --------------------------------------------------------------------------- #
# Paths / constants
# --------------------------------------------------------------------------- #
APP_DIR = Path(__file__).parent
PASSAGES_FILE = APP_DIR / "passages.json"
DB_FILE = APP_DIR / "audio_metrics.db"
RECORDINGS_DIR = APP_DIR / "recordings"

def get_setting(key, default=None):
    """Read a config value from st.secrets (Streamlit Cloud) or the environment."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


# base/small run ~real-time on CPU; medium/large want a GPU.
# Overridable on Streamlit Cloud via a secret (drop to "base" if RAM is tight).
WHISPER_MODEL_SIZE = get_setting("WHISPER_MODEL_SIZE", "small")
ENV_CHOICES = ["Quiet room", "Office", "Outdoors", "Vehicle", "Other"]
LINE_INTERVAL_S = 10  # default seconds each passage line stays before the next reveals
MAX_RECORD_S = 60     # hard cap: recording and the reading guide both stop at this
# WER at/above this (3%) flags the user to redo the reading
WER_ACCEPTABLE = 0.03

# Custom recorder+teleprompter component (records mic audio and paces the reading
# in one iframe, so the guide starts exactly when recording starts).
_recorder = components.declare_component(
    "recorder", path=str(APP_DIR / "components" / "recorder")
)


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
@st.cache_data
def load_passages():
    with open(PASSAGES_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# Audio decoding
# --------------------------------------------------------------------------- #
def decode_audio(wav_bytes):
    """Decode WAV bytes -> (mono float32 samples, sample_rate)."""
    data, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)  # average channels to mono
    return mono, sr


# --------------------------------------------------------------------------- #
# SNR — energy-based, noise floor from [pause] lines when available
# --------------------------------------------------------------------------- #
PAUSE_TOKEN = "[pause]"


def is_pause_line(line):
    return line.strip().lower() == PAUSE_TOKEN


def _pause_windows(lines, interval_s):
    """Time spans (start_s, end_s) of the [pause] lines in the paced timeline.

    The recorder advances one line every ``interval_s`` seconds starting at t=0,
    so line i occupies [i*interval_s, (i+1)*interval_s).
    """
    return [(i * interval_s, (i + 1) * interval_s)
            for i, line in enumerate(lines) if is_pause_line(line)]


def compute_snr(samples, sr, lines=None, interval_s=None,
                frame_ms=25.0, hop_ms=10.0, guard_s=1.0):
    """Energy-based SNR estimate in dB.

    If the passage has [pause] lines and the line schedule (lines + interval_s)
    is given, the noise floor is measured directly from the audio during those
    pause windows (edges trimmed by ``guard_s`` to skip breaths/co-articulation).
    Otherwise it falls back to a geometric-mean energy-percentile split.

    SNR = 10*log10((P_speech - P_noise) / P_noise).
    Returns a dict with the value plus arrays for the waveform overlay.
    """
    eps = 1e-12
    frame_len = max(1, int(sr * frame_ms / 1000.0))
    hop = max(1, int(sr * hop_ms / 1000.0))

    if len(samples) < frame_len:
        return {"snr_db": float("nan"), "note": "clip too short to frame",
                "method": "n/a"}

    n_frames = 1 + (len(samples) - frame_len) // hop
    powers = np.empty(n_frames, dtype=np.float64)
    for i in range(n_frames):
        start = i * hop
        frame = samples[start:start + frame_len]
        powers[i] = float(np.mean(frame * frame)) + eps
    frame_times = (np.arange(n_frames) * hop + frame_len / 2.0) / sr
    duration = len(samples) / sr

    # Frames falling inside [pause] windows -> measured noise floor
    pause_mask = np.zeros(n_frames, dtype=bool)
    if lines and interval_s:
        for start_s, end_s in _pause_windows(lines, interval_s):
            if start_s >= duration:
                continue
            # keep at least the middle third
            trim = min(guard_s, (end_s - start_s) / 3.0)
            s2, e2 = start_s + trim, end_s - trim
            pause_mask |= (frame_times >= s2) & (frame_times < e2)

    if pause_mask.any():
        # Noise measured from the pause windows; speech from the rest, restricted
        # to frames above the noise-derived threshold (skips within-line silences).
        p_noise = float(powers[pause_mask].mean())
        spoken = ~pause_mask
        spoken_powers = powers[spoken]
        peak = float(np.percentile(spoken_powers, 95)
                     ) if spoken_powers.size else p_noise
        threshold = np.sqrt(max(p_noise, eps) * max(peak, eps))
        speech_mask = spoken & (powers >= threshold)
        if speech_mask.any():
            p_speech = float(powers[speech_mask].mean())
        else:
            p_speech = float(spoken_powers.mean()
                             ) if spoken_powers.size else peak
        method = "pause-based (noise from [pause] lines)"
    else:
        # No usable pause windows: geometric-mean energy-percentile split
        noise_floor = np.percentile(powers, 20)
        peak = np.percentile(powers, 95)
        threshold = np.sqrt(noise_floor * peak)
        speech_mask = powers >= threshold
        noise_mask = ~speech_mask
        if not speech_mask.any() or not noise_mask.any():
            p_noise, p_speech = noise_floor, peak
        else:
            p_noise = float(powers[noise_mask].mean())
            p_speech = float(powers[speech_mask].mean())
        method = "energy percentile (no [pause] lines)"

    signal_power = max(p_speech - p_noise, eps)
    snr_db = 10.0 * np.log10(signal_power / p_noise)

    return {
        "snr_db": float(snr_db),
        "p_noise": p_noise,
        "p_speech": p_speech,
        "frame_times": frame_times,
        "power_db": 10.0 * np.log10(powers),
        "threshold_db": float(10.0 * np.log10(threshold)),
        "speech_mask": speech_mask,
        "pause_mask": pause_mask if pause_mask.any() else None,
        "speech_frac": float(speech_mask.mean()),
        "method": method,
        "note": "",
    }


# --------------------------------------------------------------------------- #
# ASR — faster-whisper (cached so the model loads once)
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Loading Whisper model…")
def get_whisper_model():
    from faster_whisper import WhisperModel
    return WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe(wav_bytes):
    model = get_whisper_model()
    segments, _info = model.transcribe(io.BytesIO(wav_bytes), language="en")
    return " ".join(seg.text.strip() for seg in segments).strip()


# --------------------------------------------------------------------------- #
# WER
# --------------------------------------------------------------------------- #
RED = "#d6455d"    # transcript: added / substituted words
BLUE = "#2f6fdb"   # reference: missing (deleted) words


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)   # strip punctuation
    text = re.sub(r"\s+", " ", text)       # collapse whitespace
    return text.strip()


def _mark(word, color):
    return f'<span style="color:{color};font-weight:600">{html_escape(word)}</span>'


def build_diff_html(out):
    """From a jiwer WordOutput, build (reference_html, transcript_html).

    Reference: words missing from the transcript (deletions) -> blue.
    Transcript: words added (insertions) and replaced (substitutions) -> red.
    Words are the normalized tokens WER is scored on.
    """
    ref_parts, hyp_parts = [], []
    for refs, hyps, aligns in zip(out.references, out.hypotheses, out.alignments):
        for c in aligns:
            r = refs[c.ref_start_idx:c.ref_end_idx]
            h = hyps[c.hyp_start_idx:c.hyp_end_idx]
            if c.type == "equal":
                ref_parts += [html_escape(w) for w in r]
                hyp_parts += [html_escape(w) for w in h]
            elif c.type == "substitute":
                # reference word left plain
                ref_parts += [html_escape(w) for w in r]
                hyp_parts += [_mark(w, RED)
                              for w in h]        # transcript word in red
            elif c.type == "insert":
                hyp_parts += [_mark(w, RED)
                              for w in h]        # added word -> red
            elif c.type == "delete":
                ref_parts += [_mark(w, BLUE)
                              for w in r]       # missing word -> blue
    return " ".join(ref_parts), " ".join(hyp_parts)


def compute_wer(reference, hypothesis):
    """Return (wer_float, details_dict). Details best-effort across jiwer versions."""
    import jiwer
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)
    details = {"substitutions": None, "deletions": None, "insertions": None,
               "hits": None, "ref_html": None, "hyp_html": None}
    try:
        out = jiwer.process_words(ref, hyp)
        details.update(
            substitutions=out.substitutions,
            deletions=out.deletions,
            insertions=out.insertions,
            hits=out.hits,
        )
        try:
            details["ref_html"], details["hyp_html"] = build_diff_html(out)
        except Exception:
            pass  # keep counts even if alignment shape is unexpected
        return float(out.wer), details
    except Exception:
        return float(jiwer.wer(ref, hyp)), details


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT,
            passage_id  TEXT,
            snr_db      REAL,
            wer         REAL,
            environment TEXT,
            notes       TEXT,
            transcript  TEXT,
            duration_s  REAL,
            audio_path  TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_session(row):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        INSERT INTO sessions
            (timestamp, passage_id, snr_db, wer, environment, notes,
             transcript, duration_s, audio_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["timestamp"], row["passage_id"], row["snr_db"], row["wer"],
            row["environment"], row["notes"], row["transcript"],
            row["duration_s"], row["audio_path"],
        ),
    )
    conn.commit()
    conn.close()


def save_wav(wav_bytes, passage_id):
    RECORDINGS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RECORDINGS_DIR / f"{passage_id}_{stamp}.wav"
    with open(path, "wb") as fh:
        fh.write(wav_bytes)
    return str(path)


# --------------------------------------------------------------------------- #
# Data export (Streamlit Cloud storage is ephemeral — let users pull data out)
# --------------------------------------------------------------------------- #
def get_sessions_rows():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM sessions ORDER BY id")]
    finally:
        conn.close()


def sessions_csv_bytes(rows):
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def export_signature():
    """Cheap fingerprint of everything the export contains, so the zip is only
    rebuilt when the data actually changes rather than on every rerun."""
    parts = []
    if DB_FILE.exists():
        s = DB_FILE.stat()
        parts.append((DB_FILE.name, s.st_size, s.st_mtime_ns))
    if RECORDINGS_DIR.exists():
        for p in sorted(RECORDINGS_DIR.glob("*.wav")):
            s = p.stat()
            parts.append((p.name, s.st_size, s.st_mtime_ns))
    return tuple(parts)


@st.cache_data(show_spinner=False)
def build_export_zip(_signature):
    """One archive with the sessions CSV, the SQLite database and every recording."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        rows = get_sessions_rows()
        if rows:
            z.writestr("sessions.csv", sessions_csv_bytes(rows))
        if DB_FILE.exists():
            z.write(DB_FILE, arcname="audio_metrics.db")
        if RECORDINGS_DIR.exists():
            for p in sorted(RECORDINGS_DIR.glob("*.wav")):
                z.write(p, arcname=f"recordings/{p.name}")
    return buf.getvalue()


def render_sidebar():
    st.sidebar.header("📥 Data export")
    st.sidebar.caption(
        "Cloud storage is temporary — download your data before the app restarts."
    )
    rows = get_sessions_rows()
    n_wavs = len(list(RECORDINGS_DIR.glob("*.wav"))) if RECORDINGS_DIR.exists() else 0
    st.sidebar.write(f"**{len(rows)}** saved session(s) · **{n_wavs}** recording(s)")
    signature = export_signature()
    st.sidebar.download_button(
        "Export all data (zip)",
        build_export_zip(signature) if signature else b"",
        "audio_metrics_export.zip",
        "application/zip",
        disabled=not signature,
        use_container_width=True,
        help="Sessions CSV, SQLite database and all recordings in a single zip.",
    )


# --------------------------------------------------------------------------- #
# Waveform figure
# --------------------------------------------------------------------------- #
def waveform_figure(samples, sr, snr):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 2.5))
    t = np.arange(len(samples)) / sr
    # Downsample for plotting if long
    step = max(1, len(samples) // 4000)
    ax.plot(t[::step], samples[::step], linewidth=0.5, color="#4C78A8")

    if "frame_times" in snr:
        times = snr["frame_times"]
        hop_t = (times[1] - times[0]) if len(times) > 1 else 0.01
        speech_mask = snr.get("speech_mask")
        pause_mask = snr.get("pause_mask")
        for i in range(len(times)):
            if pause_mask is not None and pause_mask[i]:
                ax.axvspan(times[i] - hop_t / 2, times[i] + hop_t / 2,
                           color="#2f6fdb", alpha=0.18, linewidth=0)   # measured noise
            elif speech_mask is not None and speech_mask[i]:
                ax.axvspan(times[i] - hop_t / 2, times[i] + hop_t / 2,
                           color="#54A24B", alpha=0.12, linewidth=0)   # speech
    ax.set_xlabel("Time (s)")
    ax.set_yticks([])
    title = "Waveform — green = speech"
    title += ", blue = [pause] noise floor" if snr.get("pause_mask") is not None \
        else ", white = noise floor"
    ax.set_title(title)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Recorder + paced reading guide component
# --------------------------------------------------------------------------- #
def recorder(lines, interval_s, max_s=MAX_RECORD_S, key="recorder"):
    """Render the recorder+guide iframe.

    One button starts mic capture and the paced guide together; both auto-stop
    at ``max_s`` seconds. Returns the recorded audio as a base64 WAV string,
    or None if nothing has been recorded yet.
    """
    return _recorder(lines=lines, interval_s=interval_s, max_s=max_s,
                     key=key, default=None)


# --------------------------------------------------------------------------- #
# Heavy compute, memoized per unique recording
# --------------------------------------------------------------------------- #
def process_recording(wav_bytes, reference_text, lines=None, interval_s=None):
    samples, sr = decode_audio(wav_bytes)
    duration_s = len(samples) / sr if sr else 0.0
    snr = compute_snr(samples, sr, lines=lines, interval_s=interval_s)
    transcript = transcribe(wav_bytes)
    wer, wer_details = compute_wer(reference_text, transcript)
    return {
        "samples": samples, "sr": sr, "duration_s": duration_s,
        "snr": snr, "transcript": transcript,
        "wer": wer, "wer_details": wer_details,
    }


# --------------------------------------------------------------------------- #
# Access control — password gate (Streamlit-native, backed by st.secrets)
# --------------------------------------------------------------------------- #
def check_password():
    """Return True if the user is authorized.

    The password is read from st.secrets["APP_PASSWORD"] (or the APP_PASSWORD
    env var). If none is configured, the gate is open — so local dev works
    without secrets while a deployed instance can require one.
    """
    password = get_setting("APP_PASSWORD")
    if not password:
        return True
    if st.session_state.get("password_correct"):
        return True

    def _verify():
        entered = st.session_state.get("password", "")
        if hmac.compare_digest(str(entered), str(password)):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't keep the raw password around
        else:
            st.session_state["password_correct"] = False

    st.title("Audio Metrics")
    st.caption("This app measures SNR and Word Error Rate from a read passage.")
    st.caption("Designed by M. Castanares")
    st.caption("Please enter the password to access the app.")
    st.text_input("Password", type="password", on_change=_verify, key="password")
    st.text("""By proceeding, you agree to the terms of use and privacy policy. The app temporarily captures the audio/microphone input for analysis purposes only. It does not store or share any personal data.""")
    
    if st.session_state.get("password_correct") is False:
        st.error("😕 Incorrect password.")
    
    return False


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
def main():
    st.set_page_config(page_title="Audio Metrics — SNR & WER", page_icon="🎙️")
    
    if not check_password():
        st.stop()
    init_db()
    render_sidebar()
    passages = load_passages()

    st.title("🎙️ Audio Metrics")
    st.caption(
        "Read the passage aloud in ~60 seconds. We measure SNR and Word Error Rate.")


    # 1) Environment (captured before recording) -------------------------- #
    st.subheader("Environment")
    env_choice = st.selectbox("Recording environment", ENV_CHOICES)
    env_other = ""
    if env_choice == "Other":
        env_other = st.text_input("Describe the environment")
    environment = env_other.strip() if env_choice == "Other" else env_choice

    # 2) Passage + recorder (guide starts with recording) ----------------- #
    st.subheader("Passage")
    keys = list(passages.keys())
    passage_id = st.selectbox(
        "Passage", keys, format_func=lambda k: passages[k]["title"]
    )
    passage = passages[passage_id]
    reference_text = " ".join(
        x for x in passage["lines"] if not is_pause_line(x))

    interval_s = st.number_input(
        "Seconds per line", min_value=3, max_value=30, value=LINE_INTERVAL_S, step=1,
        help="Each line lights up for this long before the next appears.",
    )
    n_pauses = sum(is_pause_line(x) for x in passage["lines"])
    pause_note = (f" {n_pauses} [pause] line(s) set the noise floor."
                  if n_pauses else "")
    st.caption(f"⏱️ One line every {interval_s}s. Recording and the guide start "
               f"together and stop automatically at {MAX_RECORD_S}s.{pause_note}")

    audio_b64 = recorder(passage["lines"], interval_s, MAX_RECORD_S)

    with st.expander("Show full passage (static)"):
        for line in passage["lines"]:
            st.markdown(f"- {line}")

    if audio_b64:
        wav_bytes = base64.b64decode(audio_b64)
        # Re-analyze when the audio, passage, or line timing changes (all affect SNR).
        compute_key = f"{hashlib.md5(wav_bytes).hexdigest()}:{passage_id}:{interval_s}"

        if st.session_state.get("compute_key") != compute_key:
            with st.spinner("Analyzing recording…"):
                result = process_recording(
                    wav_bytes, reference_text,
                    lines=passage["lines"], interval_s=interval_s,
                )
            st.session_state["compute_key"] = compute_key
            st.session_state["result"] = result
            st.session_state["wav_bytes"] = wav_bytes
            st.session_state["saved"] = False

        result = st.session_state["result"]

        # Duration sanity check
        dur = result["duration_s"]
        if dur < 45:
            st.warning(f"Clip is {dur:.0f}s — shorter than the ~60s target.")
        elif dur > 75:
            st.warning(f"Clip is {dur:.0f}s — longer than the ~60s target.")

        # 4) Results ------------------------------------------------------ #
        st.subheader("Results")
        c1, c2 = st.columns(2)
        snr_val = result["snr"]["snr_db"]
        c1.metric("SNR", f"{snr_val:.1f} dB" if snr_val == snr_val else "n/a")
        c2.metric("WER [ <3.0% acceptable]", f"{result['wer'] * 100:.1f} %")

        if result["wer"] >= WER_ACCEPTABLE:
            st.error(
                f""" ⚠️ WER is {result['wer'] * 100:.1f}%
                (≥ {WER_ACCEPTABLE * 100:.0f}%) — please redo the reading.

                Next steps:
                1. Make notes/observations that resulted in low WER;
                2. Save session; and
                3. Refresh browser.
                Note: Read the passage exactly as shown, at a steady pace."""
            )
        else:
            st.success(
                f"""✅ WER {result['wer'] * 100:.1f}% — within the acceptable range.

                Next steps:
                1. Make notes/observations that resulted in improvement;
                2. Save session; and
                3. Refresh browser. """
            )

        st.caption(f"SNR method: {result['snr'].get('method', 'n/a')}")
        if result["snr"].get("note"):
            st.caption(f"SNR note: {result['snr']['note']}")

        with st.expander("Transcript vs. reference", expanded=True):
            d = result["wer_details"]
            if d["substitutions"] is not None:
                st.caption(
                    f"hits: {d['hits']}  ·  substitutions: {d['substitutions']}  "
                    f"·  deletions: {d['deletions']}  ·  insertions: {d['insertions']}"
                )
            st.markdown(
                f"<span style='color:{BLUE};font-weight:600'>■</span> missing (reference) &nbsp;&nbsp; "
                f"<span style='color:{RED};font-weight:600'>■</span> added / substituted (transcript)",
                unsafe_allow_html=True,
            )
            box = "padding:10px 14px;border:1px solid rgba(128,128,128,.3);border-radius:8px;line-height:1.7"
            st.markdown("**Reference**")
            if d["ref_html"]:
                st.markdown(
                    f"<div style='{box}'>{d['ref_html']}</div>", unsafe_allow_html=True)
            else:
                st.write(reference_text)
            st.markdown("**Transcript (Whisper)**")
            if d["hyp_html"]:
                st.markdown(f"<div style='{box}'>{d['hyp_html'] or '<em>(empty)</em>'}</div>",
                            unsafe_allow_html=True)
            else:
                st.write(result["transcript"] or "_(empty)_")

        with st.expander("Waveform — speech vs. noise"):
            if "speech_mask" in result["snr"]:
                st.caption(
                    f"Detected speech in {result['snr']['speech_frac'] * 100:.0f}% of frames.")
                fig = waveform_figure(
                    result["samples"], result["sr"], result["snr"])
                st.pyplot(fig)
            else:
                st.write("Not enough audio to plot.")

        # 5) Notes + Save ------------------------------------------------- #
        st.subheader("Save")
        notes = st.text_area(
            "Notes", placeholder="e.g. mic clipped, background AC, retook twice")

        if st.session_state.get("saved"):
            st.success("Session saved ✓")
        elif st.button("💾 Save session", type="primary"):
            if env_choice == "Other" and not environment:
                st.error("Please describe the environment before saving.")
            else:
                audio_path = save_wav(
                    st.session_state["wav_bytes"], passage_id)
                save_session({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "passage_id": passage_id,
                    "snr_db": snr_val if snr_val == snr_val else None,
                    "wer": result["wer"],
                    "environment": environment,
                    "notes": notes.strip(),
                    "transcript": result["transcript"],
                    "duration_s": result["duration_s"],
                    "audio_path": audio_path,
                })
                st.session_state["saved"] = True
                st.rerun()


if __name__ == "__main__":
    main()
