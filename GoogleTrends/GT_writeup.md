# Challenges on the use of Google Trends for research

Internet search volumes (Google Trends) have become popular proxies for estimating current period (also referred to as "nowcasting") macroeconomic indicators. In my work on machine learning models, I've seen firsthand how these high-frequency indicators (GT variables) can circumvent the publication lags of official statistics.

However, there is a trade-off. GT variables suffer from temporal 
instability, backend scaling issues, and time-varying relevance—challenges 
that can quietly undermine model performance if left unaddressed. In this blog, I highlight some potential pros and cons on the use of Internet searches (Google Trends) for research, drawing from my work on machine learning nowcasting models.

**A. The potential** 

**Real-time data availability.** GT variables are published at high frequency (from monthly to hourly). Several studies (including our work) leverage these high-frequency indicators to nowcast the economy's growth in the current quarter. 

The figure below shows a comparison between the quarterly residential real estate property price index (rrepi), and monthly GT searches for "real estate". The data lag clearly highlights the availability of GT searches before the current quarter statistic is published. The moderate correlation between GT variable "real estate" and rrepi (r = 0.63) merits further investigation.

**Tracks cyclic/non-cycline trends.** GT variables capture cyclic patterns (elections, holidays) and unexpected shocks (natural disasters, pandemic). In the Philippines, searches for "weather" spiked during major typhoons: Haiyan (2013), Mangkhut (2018), Goni & Vamco (2020), and most recently Fung-wong (2025). The "elections" keyword reliably tracked the country's presidential and midterm cycles.

This capability of capturing both predictable trends and surprise events makes GT particularly valuable for economic monitoring. But these advantages come with significant caveats that researchers must navigate carefully.

**B. The limitation**

**Temporal instability.** GT variable series tend to fluctuate when extracted at different times of the day. This is because Google Trends only returns a subset of the dataset for a given query. Consider the plot showing the Google search index for the category "Travel". Overlaying 31 series (extracted at different times) shows small deviations (up to +3 units).

*Solution:* Aggregate multiple extractions of the series at different times of the day. This approach has been examined by Medeiros and Pires (2021). This may be another blog post in itself.

**Data shifts/scaling.** Google Trends doesn't report raw search volumes. It normalizes each series to its maximum value (0-100 scale). When recent searches surge, *historical data points get rescaled downward*, creating artificial level shifts.

This is particularly problematic when retraining models quarterly. For example, data extracted from previous quarter may suddenly look different when extracted in the current quarter if a keyword spiked recently.

*Solution:* Anchor your series to a fixed time period. Compare overlapping 
segments between old and new extractions; rescale if early periods (pre-2015) show inconsistent levels.

**Lack of stable representation/relevance.** 

Perhaps the trickiest issue: trend topics can lose meaning over time.

Take "covid" searches, for example. At the pandemic's onset (mid-2020), this keyword strongly correlated with economic downturns. But by 2023, searches had tapered significantly. Does low "covid" search volume now signal *recovery* or simply *topic disinterest*?

Several studies found that "covid" variables, despite their initial 
predictive power, caused models to overfit due to their high signal-to-noise ratio during 2020-2021. The relationship wasn't stable—it was circumstantial.

This raises broader questions: How do we model keywords whose economic 
meaning shifts? When does a GT variable stop being informative?

*Solution:* Test GT variables with different model configurations and specifications (Askitas and Zimmermann, 2009; Woloszko, 2020; Mapa et al, 2023). Use rolling-window validation set to assess whether relationships hold out-of-sample. Most importantly, exercise judgment—if a keyword's real-world relevance has faded, drop it regardless of in-sample fit.

**Final thoughts**

Google Trends is a valuable but imperfect tool. It offers 
real-time and granular information that official statistics cannot match, yet they demand careful handling: multiple extraction protocols, scaling adjustments, and continuous validation of relevance.

As economic activity leaves an ever-larger digital footprint, I think GT data will remain part of the nowcasting toolkit. The challenge for researchers is balancing technical rigor with economic intuition—knowing when these alternative indicators track the economy, and when they merely reflect noise.

<small>
Disclaimer of AI use: Claude Sonnet was used to improve the flow of the discussion.

References:

Goole Trends. "The FAQ about Google Trends". https://support.google.com/trends/answer/4365533?hl=en&ref_topic=6248052&sjid=17989609542318553445-NC

Askitas N and Zimmermann K. (2009). "Google Econometrics and Unemployment Forecasting". IZA Discussion Paper Series No. 4201. https://docs.iza.org/dp4201.pdf

Medeiros M and Pires H. (2021). "The Proper Use of Google Trends in Forecasting Models". ArXiv. econ.EM.https://doi.org/10.48550/arXiv.2104.03065

Woloszko, N. (2020), “Tracking activity in real time with Google Trends”, OECD Economics Department Working Papers, No. 1634, OECD Publishing, Paris, https://doi.org/10.1787/6b9c7518-en.

Мара CR, Armas J, Guliman ME, Castanares ML, Centeno G. (2023). A Machine Learning Approach to Constructing a Weekly GDP Tracker using Google Trends. BSP Economic Newsletter. No. 23-02. January 2023. www.bsp.gov.ph/Media_And_Research/Publications/EN23-02.pdf

RREPI data. https://www.bsp.gov.ph/Media_And_Research/Media%20Releases/2025_09/news-09262025c1.aspx

</small>
---