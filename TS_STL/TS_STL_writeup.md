"Decomposition: Breaking the signal into components"
(in progress)


# Intro:
Time series data can exhibit complex and rich patterns. It is often helpful to split a time series into several components - **trend**, **seasonality**, and **cycles** - known as "decomposition". 

Here, I will describe some of the most common methods for time-series decomposition. I will introduce python libraries (e.g., Moving averages, STL, Prophet) that I use for decomposition. My goal by the end of this blog is for us to look at complex signal thru the lense of decomposition.

# Content
**My personal experience: Breaking the problem into small parts**. 
When my wife and I bought two 37kg Ikea desks, we faced a challenge: how to transport them from the carpark to our home? Rather than struggling with the heavy boxes, we applied the "break it down" principle. We unpacked the boxes at the car and sorted components—large parts (planks, metal frames) and small parts (drawer components)—then carried them piece by piece (see photo below). This approach let us complete the move without strain, proving that breaking big problems into small, manageable pieces creates small wins toward larger goals.


**Time series components**. A time series $y_t$ can be composed of three components: a seasonal component $S_t$, a trend-cycle component $T_t$, and a remainder/residual component $R_t$. 

There are mainly two models for decomposition:

#### Additive model. The sum of the components constitute the signal

$$ y_t =  S_t + T_t + R_t $$

#### Multiplicative model. The components are multiplied together to form the signal. Multiplicative model is appropriate when the seasonal pattern/variations increases with the level of the time series.

$$ y_t = S_t \times T_t \times R_t $$ 

insight: A multiplicative model can be reduced to a linear model by applying a log transform. It is important to check the unit of measures are consistent when transforming datasets to different spaces (linear, log-spaces). In my experience, these data transforms are intermediate steps. Stakeholders would still require that the results be expressed in their original units.

\begin{align*}
    y_t &= S_t \times T_t \times R_t \quad \Longleftrightarrow \quad \log y_t = \log S_t + \log T_t + \log R_t
\end{align*}


**Data**. Lets take the Australian Export volume of Liquified Natural Gas (LNG), `AU_LNG` series, in Megaliter as an example (see photo below). 

The period 2016-2020 is referred as "the great ramp". Several mega-projects (construction of new plants) in Queensland and Western Australian which exponential increased the LNG production capacity resulting to a surge on LNG export volume. In 2020 onwards, we can observe a plateau of export volume as the plant facilities reach its normal production capacity.

**Tool 1: Moving averages** is a classical approach to extract the trend-cycle component of the series. A moving average (MA) of order $m$ is defined as

\begin{align*}
    \hat{T}_t &= \frac{1}{m} \sum_{j=-k}^{k} y_{t+j}
\end{align*}

where $m = 2k + 1$. In other words, the estimate of the trend-cycle at time $t$ is obtained by averaging the time series values within $k$ periods of $t$. This is also known as a centered moving average or an $m-$MA.

The figure below shows the resulting 6-month and 12-month MA of the `AU_LNG`. Note that a larger order $m$ results to a smoother series emphasizing more the trend component.


**Tool 2: Seasonal Trend Decomposition using LOESS (STL) decomposition**
Developed by R.B. Cleveland et al (1990), this method is a versatile and robust method for decomposition. LOESS (locally estimated scatterplot smoothing) is a method for estimating nonlinear relationships.

The key advantages of STL are:
* Allows for the seasonal component to change over time wherein the rate of change can be controlled by the user
* Smoothness of the Trend-cycle can also be set by the user
* It is robust to outliers and will be part of the remainder.

We can use Python statsmodels library to carry-out STL decomposition. The figure below shows the resulting trend, cycle, and residual component after applying STL (Panel a). The seasonal plot showing the levels of the seasonal component for the same month cross different years also indicate how robust/predictable the cyclic pattern is. Ideally, the levels of cyclic component would be the same for the same month but real-world data always tend to deviate from ideal assumptions. 

**insight:** To check for the quality of the decomposition, we can look at the auto-correlation function (ACF) of the residual. The ACF shows that there are significant auto-correlations of the residual at its 1-month, 3-month, and 8-month lag. This suggest that there is still some information(signal) that were not captured. Researchers can fine-tune the STL parameters or explore other decomposition methods.

See the statsmodels [API](https://www.statsmodels.org/stable/examples/notebooks/generated/stl_decomposition.html) for details of the parameters.

**Tool 3: Prophet Model**
Introduced by Facebook  ([S. J. Taylor & Letham, 2018](https://doi.org/10.1080/00031305.2017.1380080)). An pre-print of the paper can be found [here](https://peerj.com/preprints/3190v2.pdf). [Prophet](https://facebook.github.io/prophet/) is a procedure for forecasting time series data based on an additive model where non-linear trends are fit with yearly, weekly, and daily seasonality, plus holiday effects.


Prophet can be viewed as a nonlinear regression model of the form:

\begin{align*}
    y_t &= g(t) + s(t) + h(t) + \varepsilon_t
\end{align*}

where:
- $g(t)$ is the trend function, which models non-periodic changes. By default, it is a piecewise-linear "growth term."
- $s(t)$ describes the seasonal patterns (e.g., yearly, weekly)
- $h(t)$ represents the effects of holidays or other irregular events.
- $\varepsilon_t$ is the error term, assumed to be white noise.

We applied Prophet model to the `AU_LNG` series (see Figure below). We also included Australian Holidays (number of holidays in a month) as an additional regressor, e.g., New Year's Day, Australia Day, Holy Week, ANZAC Day, etc. 

Comparing with the previous results using STL, we find the same trend extracted by Prophet. However, the variation (amplitude) in the seasonal and residual components are smaller compared to STL. The ACF of the residual also shows significant auto-correlation at lag 1-month only.

**insights**. 
Most linear regression models commonly assumes that the residuals have zero auto-correlation and are normally distributed. However, real world data often deviates from these assumptions. Modelling data with some auto-correlation in the residuals woudd result to inefficient forecast - as there are some information left unaccounted. As discussed by [Hyndman and Athanasopoulos](https://otexts.com/fpp2/regression-evaluation.html), the forecasts resulting from these models are still unbiased - "meaning they are not wrong" but will usually have larger prediction intervals than they need to.

After decomposng the signal to its components, we are now primed to investigate several models to capture the characteristics of the trend-cycle, and seasonal component (and even the residual). For example, the trend component can be modeled using an exponential smoothing, naive, or moving averages that just captures to long-term behavior. The seasonal component may also be modeled as a seasonal naive - taking the level the same as last year of the same month. The residual component may be modeled using an Auto-regressive (AR) model taking into account the significant lags in the ACF.

**Final thoughts**
Decomposition transforms complex time series into interpretable components—trend, seasonality, and residuals. Like breaking down an Ikea desk into manageable pieces, decomposition reveals the underlying structure of your data.

The three tools explored here offer different trade-offs:
- **Moving averages**: Simple, intuitive, but limited to trend extraction
- **STL**: Flexible and robust, ideal when seasonality evolves over time
- **Prophet**: Best for business forecasting with holidays and multiple seasonalities

Always inspect the residual's ACF. Significant autocorrelation signals that patterns remain uncaptured—opportunities for model refinement or alternative approaches. Once decomposed, each component can be modeled separately (exponential smoothing for trend, seasonal naïve for cycles, AR models for residuals) before recombining for forecasts.

**Bringing the pieces together**. Ending with the Ikea story, here is a photo of the two desks after assembly. It is currently my workspace at home and has this library vibe to it.

Decomposition isn't just a preprocessing step—it's a lens for understanding what drives your time series.

Codes used to generate the figures may be found here: [View Code Repository on GitHub]()

Disclaimer of AI use: Claude Sonnet was used to improve the flow of the discussion.

references:

https://data.gov.au/data/dataset/australian-petroleum-statistics
https://otexts.com/fpp2/regression-evaluation.html
https://peerj.com/preprints/3190v2.pdf