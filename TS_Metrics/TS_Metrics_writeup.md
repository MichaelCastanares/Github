What information can we extract from a time series?

(in progress)

# Intro:
Time series data tells compelling stories about the past and hints at the future. Will housing prices in Australia continue rising? When does Australia see peak tourist arrivals? Understanding these patterns is vital for policy-making and business strategy.

While time series analysis can seem daunting, specialized tools like Python's `tsfeatures` package make it accessible. In this post, I'll share practical metrics for characterizing time series—tools I've used in my work and MSDS studies to as pre-cursor analysis towards building time-series models.

Let's test our prior knowledge of time-series features with the figure below. Can we describe some features in the time-series? What are some possible research questions we can further investigate?



The time-series is the "number of nights stayed" by Australian resident in a particular state. The data is sourced from the National Visitor Survey (Tourism Research Australia)

# Content
**Decomposition**. A time-series can be decomposed into three components: Trend, Seasonal/Cyclic, and Innovations/Noise. The decomposition can either be linear or multiplicative. A linear decomposition can be written as

$$Y_t = T_t + S_t + \varepsilon_t$$

Where:
- $T_t$ = Trend
- $S_t$ = Seasonal/Cyclic component  
- $\varepsilon_t$ = noise/innovation

**Seasonality, and Cyclicity**. A time series is seasonal when it exhibits a regular, fixed pattern that aligns with the calendar (e.g., quarterly, annual) or weather  (e.g., summer, winter). Meanwhile, cyclic series exhibits patterns that follows other than calendar dates or season (e.g., business cycles, market cycles in Economics).

- insights: Seasonal and cyclic patterns in the series are straight forward to model due to their regularity. Take the tourism data of Tasmania. Plotting the seasonal plot (stacking the time-series per year) shows that most tourist visits happen during January (Summer). Meanwhile, September (start of spring) show the least volume of tourist visits - suitable for those who want to avoid the crowd.

**Trend**. Trend describes the general long-term movement of the time series whether its increasing, decreasing, or no change. As human, we also tend to think (or follow a straight path). We should be weary that when seeing an increasing series follow several paths (in the time steps): linearly increase, exponentially increase, exponential decrease, or remains the same.


- insights: A simple way to extract a trend in the series is to take a moving average.

In `tsfeatures`, we can calculate the strength of trend and seasonality. A parametric plot of the strength of trend and seasonality can be a straightforward analysis to assess several time series.





**Auto-correlation**. It's akin to "memory of the time series" - to what extent do past (or lagged) values are linearly related to the present values. Consider the simple example (an AR1 relation)

$$y_t = \alpha y_{t-1} + \varepsilon$$

Where $\alpha$ (the AR1 coefficient) captures the influence of the previous time step.

This is common but powerful relation which says that the present value is determined by a factor $\alpha$ of the recent past value ,$y_{t-1}$, and some noise, $\eta$. The AR1 coefficient, $\alpha$ can be estimated using an auto-correlation function (taking lag = 1)

- insights: In my work, I found that AR1 is typically a good baseline model that is hard to beat. It is elegant, powerful, and easy to explain. 

**Stationarity**. A series is stationary when its statistical properties (mean, variance) don't change over time. Most (linear) forecasting/statistical models assume/requires that the series is stationary. Statistical test for stationarity are Augmented Dickey-Fuller test and KPSS test.

- insights: Most real-world time series tend to be non-stationary. Data pre-processing (e.g. taking the first-difference or growth rates) are often required before applying statistical models. Interestingly, complex machine learning models (e.g., Neural Networks and XGBoost) does not require the series to be stationary.

**Entropy**. This refers to the predictability (randomness) of the data. A Shannon spectral entropy metric has a value 0 for series with clear trend and seasonality and value close to 1 for noisy series.

- insights: Use entropy to assess data quality and preprocessing effectiveness. Lower entropy after cleaning indicates better signal extraction.

Summary:


Data:
Air Travel
Real Estate prices

Code:

references

https://www.youtube.com/watch?v=rcdDl8qf0ZA
https://otexts.com/fpp2/#