import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque


#### SET SEED
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

class StudentMarkovLearner:
    def __init__(self, states=['A', 'B', 'C', 'D', 'E'], forget_factor=0.95):
        self.states = states
        self.state_to_idx = {s: i for i, s in enumerate(states)}
        self.n = len(states)
        self.forget_factor = forget_factor
        # Initial state: All zeros (Stage 5)
        self.matrix = np.zeros((self.n, self.n))
        
    def update(self, current_char, next_char):
        """Update weights based on observed transition (Stage 1 & 3)."""
        i, j = self.state_to_idx[current_char], self.state_to_idx[next_char]
        
        # Apply forgetting factor to the entire matrix
        self.matrix *= self.forget_factor
        
        # Reinforce the observed transition (Weighted learning)
        self.matrix[i, j] += 1
        
        #convert to probabilities
        self.matrix = self.matrix / (self.matrix.sum(axis=1, keepdims=True)+1e-8)

    def predict(self, current_char):
        """Predict the next state stochastically (Stage 2 & 4)."""
        i = self.state_to_idx[current_char]
        row = self.matrix[i]
        
        if np.sum(row) == 0:
            # If nothing learned yet, pick randomly
            return np.random.choice(self.states)
        
        # Normalize row to create a probability distribution
        probabilities = row / np.sum(row)
        return np.random.choice(self.states, p=probabilities)

    def get_matrix_df(self):
        """Returns the adjacency matrix as a readable DataFrame."""

        return pd.DataFrame(self.matrix, index=self.states, columns=self.states)
    
    def study(self, sequence):
        """Study a sequence of transitions."""
        for i in range(len(sequence) - 1):
            curr, nxt = sequence[i], sequence[i+1]
            
            # Before learning, let's see what the student predicts
            prediction = self.predict(curr)
            
            # Student learns the actual transition
            self.update(curr, nxt)

def generate_sequence(matrix, states, length=100):
    sequence = ["A"] # Start at a random letter
    for _ in range(length - 1):
        curr_idx = states.index(sequence[-1])
        # Sample the next letter based on ground truth probabilities
        next_char = np.random.choice(states, p=matrix[curr_idx])
        sequence.append(next_char)
    long_str = "".join(sequence)

    #split the long string into chunks of varying lengths (1 to 5)
    chunks = []
    i = 0
    while i < len(long_str):
        chunk_length = np.random.randint(3, 5) # Random chunk length between 3 and 5
        chunks.append(long_str[i:i+chunk_length])
        i += chunk_length

    return chunks

def plot_transition_network(matrix, states, title="Ground Truth Transition Network"):
    graph = nx.DiGraph()

    for source_index, source_state in enumerate(states):
        for target_index, target_state in enumerate(states):
            weight = matrix[source_index, target_index]
            if weight > 0:
                graph.add_edge(source_state, target_state, weight=weight)

    positions = nx.circular_layout(graph)
    edge_weights = [graph[u][v]["weight"] for u, v in graph.edges()]
    edge_widths = [1 + 6 * weight for weight in edge_weights]

    plt.figure(figsize=(5, 5))
    nx.draw_networkx_nodes(
        graph,
        positions,
        node_size=2200,
        node_color="#f4f7fb",
        edgecolors="#1f2d3d",
        linewidths=1.5,
    )
    nx.draw_networkx_labels(graph, positions, font_size=14, font_weight="bold")
    nx.draw_networkx_edges(
        graph,
        positions,
        arrowstyle="->",
        arrowsize=20,
        width=edge_widths,
        edge_color="#4c72b0",
        connectionstyle="arc3,rad=0.12",
    )

    edge_labels = {(u, v): f"{d['weight']:.1f}" for u, v, d in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, positions, edge_labels=edge_labels, font_size=10)

    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.show()

class MarkovLearner2:
    """
    Empirical Markov Learner with emotional engagement states.
    
    Tracks observation counts with exponential forgetting and models:
    - BOREDOM: When too many correct answers (low challenge)
    - FRUSTRATION: When too many mistakes (high difficulty)
    - OPTIMAL ENGAGEMENT: Sweet spot around 50-70% accuracy
    """
    def __init__(self, states=['A', 'B', 'C', 'D', 'E'], forget_factor=0.95, alpha=1.0, 
                 window_size=20, boredom_threshold=0.8, frustration_threshold=0.3):
        """
        Args:
            states: List of state names
            forget_factor: Decay rate for observation counts (0-1)
            alpha: Dirichlet prior strength
            window_size: How many recent trials to consider for engagement state
            boredom_threshold: Accuracy above this → BORED (reduced learning)
            frustration_threshold: Accuracy below this → FRUSTRATED (reduced learning)
        """
        self.states = states
        self.state_to_idx = {s: i for i, s in enumerate(states)}
        self.n = len(states)
        self.forget_factor = forget_factor
        self.alpha = alpha
        
        # Performance tracking for engagement state
        self.window_size = window_size
        self.boredom_threshold = boredom_threshold
        self.frustration_threshold = frustration_threshold
        self.recent_performance = deque(maxlen=window_size)  # True=correct, False=incorrect
        
        # Emotional state history
        self.engagement_history = []
        
        # Track COUNTS of each transition
        self.observation_counts = np.ones((self.n, self.n)) * alpha
        self.learned_matrix = self.observation_counts.copy() / self.observation_counts.sum(axis=1, keepdims=True)
        
    def compute_engagement(self):
        """
        Compute emotional engagement state based on recent accuracy.
        
        Returns:
            engagement_factor (0-1): Multiplier for learning rate
            state (str): 'bored', 'frustrated', or 'optimal'
            accuracy (float): Recent accuracy % 
        """
        if len(self.recent_performance) == 0:
            return 1.0, 'neutral', 0.5
        
        accuracy = sum(self.recent_performance) / len(self.recent_performance)
        
        if accuracy > self.boredom_threshold:
            # BORED: Too easy, not engaging. Reduce learning by up to 50%
            engagement_factor = 0.5 + 0.5 * (1 - (accuracy - self.boredom_threshold) / (1 - self.boredom_threshold))
            state = 'bored'
        elif accuracy < self.frustration_threshold:
            # FRUSTRATED: Too hard, giving up. Reduce learning by up to 50%
            engagement_factor = 0.5 + 0.5 * (accuracy / self.frustration_threshold)
            state = 'frustrated'
        else:
            # OPTIMAL: Sweet spot. Learn at full rate, peak at 50-70%
            mid_point = (self.frustration_threshold + self.boredom_threshold) / 2
            distance = abs(accuracy - mid_point)
            max_distance = mid_point - self.frustration_threshold
            engagement_factor = 1.0 - 0.3 * (distance / max_distance)  # Up to 30% boost at sweet spot
            state = 'optimal'
        
        return engagement_factor, state, accuracy
        
    def update(self, current_char, next_char, was_correct):
        """Updates observation counts modulated by emotional engagement."""
        i = self.state_to_idx[current_char]
        j = self.state_to_idx[next_char]
        
        # Track performance for engagement
        self.recent_performance.append(was_correct)
        
        # Get current engagement state
        engagement_factor, state, accuracy = self.compute_engagement()
        self.engagement_history.append({'state': state, 'engagement': engagement_factor, 'accuracy': accuracy})
        
        # Apply exponential decay to all counts
        self.observation_counts *= self.forget_factor
        
        # Reinforce the Dirichlet prior
        self.observation_counts += self.alpha * (1 - self.forget_factor)
        
        # Increment the transition count, scaled by engagement
        # High engagement = stronger learning signal
        self.observation_counts[i, j] += engagement_factor
        
        # Recompute the learned probabilities
        self.learned_matrix = self.observation_counts.copy() / self.observation_counts.sum(axis=1, keepdims=True)
        
    def predict(self, current_char):
        """Prediction based on the student's learned probabilities."""
        i = self.state_to_idx[current_char]
        
        learned_row = self.learned_matrix[i]
        
        if learned_row.sum() == 0:
            return np.random.choice(self.states)
        
        probs = learned_row / learned_row.sum()
        return np.random.choice(self.states, p=probs)

    def study(self, sequence):
        """Process a sequence and return results with engagement tracking."""
        results = []
        for i in range(len(sequence) - 1):
            curr, nxt = sequence[i], sequence[i+1]
            prediction = self.predict(curr)
            was_correct = (prediction == nxt)
            
            self.update(curr, nxt, was_correct)
            results.append((was_correct, curr+prediction))
        return results

    def get_learned_df(self):
        """Returns the student's learned probability matrix."""
        return pd.DataFrame(self.learned_matrix, index=self.states, columns=self.states)
    
    def get_obs_df(self):
        """Returns the raw observation counts."""
        return pd.DataFrame(self.observation_counts, index=self.states, columns=self.states)
    
    def get_engagement_stats(self):
        """Returns recent engagement statistics."""
        if not self.engagement_history:
            return {}
        
        recent = self.engagement_history[-self.window_size:]
        states = [e['state'] for e in recent]
        engagements = [e['engagement'] for e in recent]
        accuracies = [e['accuracy'] for e in recent]
        
        return {
            'current_state': states[-1] if states else 'neutral',
            'current_engagement': engagements[-1] if engagements else 1.0,
            'current_accuracy': accuracies[-1] if accuracies else 0.5,
            'avg_engagement': np.mean(engagements),
            'state_counts': {
                'bored': states.count('bored'),
                'frustrated': states.count('frustrated'),
                'optimal': states.count('optimal')
            }
        }