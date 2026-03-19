### "Linear Model: Autoregressive Integrated Moving Average (ARIMA)"

19 March 2026

Model building is one of the most exciting and critical aspects of time-series forecasting. The key question we grapple with is: "What model best captures the underlying patterns in our time series?" To develop this intuition, we need to get our hands dirty and explore different modeling approaches.

In this blog, I discuss ARIMA — a linear model widely used in time-series forecasting in economics, finance, among others. We will explore the application of ARIMA to different time-series and how it performs against naive models. My goal is to provide a concise overview of the theoretical foundations while demonstrating practical applications using python packages such as Statsforescast and the NIXTLA.


**Data**. We will analyze three time series, namely:
1. AUD/PH Exchange rate daily series from [Reserve Bank of Australia](https://www.rba.gov.au/statistics/historical-data.html#exchange-rates);
2. AU inflation rate from [Reserve Bank of Australia](https://www.rba.gov.au/statistics/tables/xls/g01hist.xlsx?v=2026-03-08-20-14-13); and
3. Crude oil prices downloaded from [Federal Reserve Bank of St. Louis](https://fred.stlouisfed.org/series/DCOILWTICO).

These macroeconomic indicators are important metrics that capture economic conditions. In particular, crude oil prices has been surging (as of this writing) due to the War/Conflict in the middle east. Forecasting trends of crude oil prices amid this war crisis will support policymakers, economic managers, business, and consumers in making sound and effective decisions.


### A. Theoretical Foundations

#### A.1 ARIMA
ARIMA is a model that captures different temporal structures in a time series. It is comprised of three components/sub-models, namely: Autogression (AR), differencing (I), and Moving Averages (MA). The submodels are specified using parameters (also referred to as the order of the ARIMA), ($p, d, q$,).

ARIMA model assumes the following:

*(1) Time series is stationary*, i.e., the statistical properties such as mean and variance do not change over time;

*(2) Linearity*, i.e., the model relies that future values can be modelled as linear combination of past values and errors; and

*(3) No seasonal effects*, i.e., the standard ARIMA does not take into account seasonality of the data; however, this can be extended by addition of seasonal terms to reflect periodic variations resulting to Seasonal ARIMA (SARIMA) models.

Next, I describe the three components/sub-models.

###### Component 1: AR(p) model
Consider modelling $X_t$ using its lag values. ARIMA(p,0,0) is equivalent to AR(p) which relates $X_t$ and its $p$ lag values of $X_t$, i.e., ${X_{t-1},... X_{t-p}}$ with some weights $\alpha_i$.

$$ 
X_t = \mu + \sum_{i=1}^p{\alpha_iX_{t-i}}
$$

###### Component 2: Integrated model
The integrated model uses differencing (taking the difference of two consecutive observations) of order $d$ to make the series stationary before ARIMA. 

ARIMA(0,1,0) is the just the first difference equation. This also corresponds to a random walk process.
$$ 
    X_t = X_{t-1} + \epsilon_t
$$

ARIMA(0,2,0)
$$
X_t = 2X_{t-1} + X_{t-2} + \epsilon_t + \epsilon_{t-1}
$$


[Hyndman et al](https://otexts.com/fpppy/nbs/09-arima.html) discussed the use of a backshift operators $B$ to express the differencing. The backshift operator is defined as
$$
BX_t = X_{t-1}
$$
So the first difference is expressed as,
$$
X_{t} - X_{t-1} = X_{t} - BX_{t} = (1-B)X_t
$$
Likewise, the second difference is 
$$
X_t - 2X_{t-1} + X_{t-2} = (1-2B + B^2)X_t = (1-B)^2 X_t  
$$
In general, the $d$ order differencing can be expressed as
$$
(1-B)^dX_t
$$

> **insight**. When handling a series that is non-stationary series, takin First-order differencing ($d=1$)  is sufficient to make the series stationary. Futhermore, taking the first order log-difference (equivalent to taking the growth rates) helps stabilize any variations in the mean resulting to a stationary series in log-scale.

##### Component 3: Moving Average model
The moving average component captures the influence (weighted by coefficient $\theta$) of past residuals or errors of order $q$ to the observation. It is written as

ARIMA(0,0,q):
$$
X_t = \epsilon_t + \theta \epsilon_{t-1} + \ldots + \theta_{q} \epsilon_{t-q}
$$


##### ARIMA in a compact form
>Now, we can write the ARIMA model is a more compact form.
>
>$$
(1-\alpha _1B - \ldots - \alpha _pB^p)(1-B)^dX_t = c + (1 + \theta_1B + \ldots + \theta_qB^q) \epsilon_t
>$$
>
>Alternatively,
>
>$$
\hat{X}_t = c + \sum_{i=1}^p{\alpha_i\hat{X}_{t-i}} + \sum_{j=1}^{q}{\theta_j\epsilon_{t-j}} + \epsilon_t
>$$
>This defined an ARIMA(p,d,q) with a drift $\mu$ where
>$$
>\mu = \frac{c}{1-\sum{\theta_i}}
>$$

#### A.2 Tests for stationarity
The two formal tests for stationarity are: the augmented Dickey-Fuller (ADF) and Kwiatkowski-Phillips-Schmidt-Shin (KPSS) test.

ADF Null hypothesis (H0): the series is non-stationary.

KPSS (HO): the series is stationary.

These tests are designed to test for trend stationary. It is important to remove any seasonality in the series first to avoid false positives/negatives.

#### A.3 Loss function: Information Criteria
Given the ARIMA model, we ask, "how do we determine the the appropriate (p,d,q)?" Typically, we find the optimal (p,d,q) that minimizes a loss or objective function, i.e., Root Mean Square Error (RMSE) or Maximum Likelihood estimate. Instead, information criteria are used as they balance model fit with complexity to avoid overfitting. Information Criteria such as the Akaike Information Criterion (AIC) or Bayesian Information Criterion (BIC) penalizes the addition of model parameters favoring simpler models.

$$
AIC = 2K - 2\ln(L)
$$

$$
BIC = -2k\ln(L) + k\ln(n)
$$

where $K$ is the number of parameters, $\ln(L)$ is the log-likelihood and $n$ is the sample size.


There are two ways either by greedy Grid search - trying different combinations of (p,q,d) which optimizes the AIC or BIC. Alternatively, we can utilize developed algorithms such as the AutoARIMA by Hyndman & Khandakar, 2008.


#### A.4 Static versus Dynamic forecast

Static forecast (also referred to as one-step ahead forecast) uses the present and historical values of $X_t$ to forecast $X_{t+1}$. 

In contrast, dynamic forecast utilizes the actual historical and present values $\{X_{t-j}, ...,  X_{t-1},....X_{t}\}$ and model estimates of future values $\{\hat{X}_{t+1}, ..., \hat{X}_{t+h-1}\}$ to forecast h-steps ahead $\hat{X}_{t+h}$.

Intuitively, errors/uncertainty in the dynamic forecast tend to increase with longer horizon as errors of the model estimates compound.

### B. Applications
Now, we apply ARIMA on three time-series: AUD/Php exchange rate, AU inflation rate, and Crude Oil price. First, let us develop our "intuition muscle".

#### B.1 Model Intuition from the ACF plots
Examine the plot below which shows the time-series, first-difference series, and the Auto-correlation function of the first-differenced series. Without any coding, can we make an a good guess on what could be the appropriate ARIMA model for each case and why.


<img src="Blog_ARIMA_1.png?raw=true"/>


> Hypothesis:
>
> We can say that the three series are now stationary, i.e., each has a trend and significant auto-correlations of its lag values.
> 
> **AUD/PHP series**. From the ACF plot, the first-differenced series show no significant auto-correlations with lags. Taking the first difference of the series was sufficient to remove seasonality and any relation with the past value of the exchange rate. Thus, I would guess that ARIMA(0,1,0) would be a good model for the AUD/PHP exchange rate.
> 
> **AU Inflation rate series**. The ACF plot of the first-difference series show a signification correlation with lag 1-quarter. ARIMA(1,1,0) would be a good candidate model.
> 
> **Crude oil series**. The WTI series shows an interesting patterns. The series shows some cyclic patterns. Also, there is an observed significant auto-correlation of the the first-differenced series and its lags. ARIMA(7,1,0) may be a good starting model.
> 
> 

#### B.2 Evaluation Strategy

We want to forecast the next time-steps, i.e., 30 days for daily, 4 quarters for quarterly data. We will follow a 5-step strategy to evaluate the model (see Table below)

**Table. Model evaluation Strategy**
1. Split the data into train-val-test;
2. Test for stationarity;
3. Fit ARIMA and Naive models;
4. Forecast (h-step dynamic and 1-step iterative static forecast); and
5. Evaluate forecast errors.


#### B.3 Results

The figure below shows the results of the 5-step evaluation strategy for the AUD/PHP exchange rate. Stationary Tests (ADF and KPSS Tests) show that the first-differenced of the series is stationary. Applying AutoARIMA, the optimal (p,d,q) coefficients using AIC or BIC is ARIMA (0,1,0) which is a random walk model. This is also confirmed with 30-day ahead forecast evaluation where RWD was the best model (MAE = 0.84 unit). My initial guess of ARIMA(1,1,1) showed also comparable performance with RWD model. 

Focusing on the panel: 30-day forecast of models, we can see that the dynamic forecast is just a straight line with error bands increasing at the horizon. Suppose we want to track the progression of the exchange rate, we can shorten the forecast horizon (say $h$ = 1 day) and refit the model in a 1-day sliding window, i.e., generate new estimates as we incorporate recent data. The resulting 1-day ahead iterative forecast is shown in the lower right panel.
<img src="Blog_ARIMA_2.png?raw=true"/>

The iterative forecast is now able to track the trend of the exchange rate. Naive model still outperforms our guess ARIMA model (1,1,1). Examining the other series, we find that Auto-ARIMA model converges to a ARIMA(0,1,0) or RWD. For the AU inflation rate, our guess model ARIMA (1,1,0) perform slightly better than Naive. Overall, Naive model show consistently robust performance across the three series.

<img src="Blog_ARIMA_3.png?raw=true"/>

The table below summarizes our findings.

|  | AUD/PHP Exchange rate | AU Inflation Rate | Crude Oil Prices |
|:---------|:----------------------:|:-------------------:|:------------------:|
| first-differenced is stationary| Y | Y | Y |
| **MAE (1-step ahead)** | 
| Naive | **0.18** | 0.12 | **1.05** |
| RWD | 0.18 | 0.12 | 1.05 |
| AutoARIMA | 0.18 | 0.11 | 1.05 |
| User-defined ARIMA | 0.18 | **0.10** | 1.14 |

Source: Author's estimates

> **insights**: "Why ARIMA did not perform as good as Naive model? How can we improve the models?"
> This exercise shows that Naive models can be hard to beat. Exchange rates and prices exhibit [Martingale pricing](https://en.wikipedia.org/wiki/Martingale_pricing) - expected future price of the stock, given all available information, is the same as the current price. After first differencing, our series lost most autocorrelations, leaving little for ARIMA to exploit beyond what simpler models (Naive, RWD) already capture. 
>
> We may improve the model by adding exogenous regressors (resulting to ARIMAX, etc) to capture surprises/shocks such as the geopolitical events driving the crude oil prices (see Figure below). For longer horizons or more seasonal data, ARIMA would likely outperform. Finally, non-linear models may better capture market complexities that linear models cannot.

<img src="Blog_ARIMA_4.png?raw=true"/>

### Final thoughts

This analysis demonstrates that while ARIMA models provide a theoretically grounded framework for time-series forecasting, simpler approaches like the Naive model often provide competitive or superior performance. The key insight is not that ARIMA should be dismissed, but rather gain intuition on how it works and why it did not work. I think the best way to learn is to be exposed with different models.

Codes used to generate the figures may be found here: [View Code Repository on GitHub](https://github.com/MichaelCastanares/Github/tree/main/TS_ARIMA)


Disclaimer of AI use: Claude Sonnet was used to improve the flow of the discussion.


### Reference:

https://nixtlaverse.nixtla.io/statsforecast/docs/getting-started/getting_started_complete.html
https://otexts.com/fpppy/nbs/09-arima.html
https://en.wikipedia.org/wiki/Martingale_pricing