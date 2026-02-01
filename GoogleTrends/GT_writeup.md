### Challenges on the use of Google Trends for research

In this blog, I highlight some potential pros and cons on the use of Internet searches (Google Trends) for research, drawing from my work on machine learning nowcasting models. Internet search volumes (i.e., Google Trends variables) serve as proxies to forecast macroeconomic indicators with publication lags. However, GT variables suffer from data quality issues, data shifts, scaling problems, and lack of representation. Several workarounds have been applied by other studies, such as data averaging/resampling, rescaling, and careful model training and specification. Understanding these limitations will help researchers (like me) be aware and cautious when using GT variables in modeling.


**A. The potential** 

**Captures cyclic trends.** GT variables capture cyclic (and not-so-cyclic) patterns of weather and national interest. The time-series for the keyword "weather" shows several peaks corresponding to supertyphoons that hit the Philippines such as: Haiyan (2013), Mangkhut (2018), Goni & Vamco (2020), Trami (2024), and Fung-wong (2025). Similarly, the search word "elections" tracks the regular presidential and midterm elections in the Philippines.

**Real-time data availability.** GT variables are published at high frequency (from monthly to hourly), circumventing publication lags of official statistics. Several studies (including our work) leverage these high-frequency indicators to estimate (or "nowcast") the economy's growth in the current quarter. The figure below shows a comparison between the real property price index (BSP), rrepi, and GT searches for "real estate". Whether the GT variable "real estate" tracks rrepi merits further investigation (simple serial correlation of r = 0.63).

**B. The limitation**

**Temporal instability.** GT variable series tend to fluctuate (±5 units) when extracted at different times of the day. Google Trends only returns a subset of the dataset for a given query. Consider the plot showing the Google search index for the category "Travel". Overlaying 31 series (extracted at different times) shows small deviations (up to +3 units).

*Solution:* Aggregate multiple extractions of the series at different times of the day. This approach has been examined by Medeiros and Pires (2021). This may be another blog post in itself.

**Data shifts/scaling.** Google Trends does not return the actual level/volume of searches. On the backend, a sampled GT variable series is normalized to the maximum search volume within the subset, resulting in a relative Google search volume index. This backend-scaling procedure can cause artificial data shifts, particularly when recent searches of a keyword/category/topic are high.

*Solution:* Check whether early data segments (e.g., 2014 and earlier) from recent extractions are consistent in levels with the training set. If not, rescaling/adjustment should be applied.

**Lack of stable representation/relevance.** Trend topics may be relevant only during a given period. For example, searches for "covid" showed strong interest at the onset of the COVID-19 pandemic (mid-2020) and then tapered in 2023. Several studies have used "covid" searches to capture economic downturns; however, some researchers suggest avoiding it as the high signal-to-noise ratio tends to overfit models.

As a researcher, I often wonder: Does a decrease in "covid" searches signal better economic conditions? After 2023, does this view still hold? Will searches for "covid" be irrelevant in the future?

*Solution:* Test GT variables with different model configurations and specifications (Askitas and Zimmermann, 2009; Woloszko, 2020; Mapa et al, 2023). Exercise judgment on temporal relevance.

Indeed, Google Trends variables present a double-edged sword for economic research. While they offer real-time insights and can capture economic sentiment at high frequencies, researchers must navigate their inherent limitations—temporal instability, scaling inconsistencies, and time-varying relevance. The key to leveraging GT data effectively lies in understanding and addressing these challenges through robust methodology: multiple data extraction protocols, appropriate rescaling techniques, and well-thought-out model specifications. As the digital footprint of economic activity continues to grow, GT variables will remain a valuable, albeit imperfect, tool in the researcher's toolkit—one that requires both technical rigor and economic judgment to use effectively.


References:

Goole Trends. "The FAQ about Google Trends". https://support.google.com/trends/answer/4365533?hl=en&ref_topic=6248052&sjid=17989609542318553445-NC

Askitas N and Zimmermann K. (2009). "Google Econometrics and Unemployment Forecasting". IZA Discussion Paper Series No. 4201. https://docs.iza.org/dp4201.pdf

Medeiros M and Pires H. (2021). "The Proper Use of Google Trends in Forecasting Models". ArXiv. econ.EM.https://doi.org/10.48550/arXiv.2104.03065

Woloszko, N. (2020), “Tracking activity in real time with Google Trends”, OECD Economics Department Working Papers, No. 1634, OECD Publishing, Paris, https://doi.org/10.1787/6b9c7518-en.

Мара CR, Armas J, Guliman ME, Castanares ML, Centeno G. (2023). A Machine Learning Approach to Constructing a Weekly GDP Tracker using Google Trends. BSP Economic Newsletter. No. 23-02. January 2023. www.bsp.gov.ph/Media_And_Research/Publications/EN23-02.pdf

RREPI data. https://www.bsp.gov.ph/Media_And_Research/Media%20Releases/2025_09/news-09262025c1.aspx