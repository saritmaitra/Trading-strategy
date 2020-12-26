# -*- coding: utf-8 -*-
"""trading strategy.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1POMIZVryYxNec_9ZVLeeiDKm0PdV68sn
"""

# Commented out IPython magic to ensure Python compatibility.
!pip install pyforest
from pyforest import *
import datetime, pickle, copy
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)
import matplotlib.pyplot as plt
# %matplotlib inline  
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
!pip install quandl
import quandl
plt.style.use('ggplot')
!pip install yfinance
import yfinance as yf

QUANDL_KEY = 'LSQpgUzwJRoF667ZpzyL'
quandl.ApiConfig.api_key = QUANDL_KEY
# NYMEX WTI Crude Oil futures (CL)
df = quandl.get(dataset='WIKI/CL',
                       start_date='2000-01-01')
df

"""The result of the request is a DataFrame (2,643 rows) containing the daily OHLC
prices, the adjusted close prices.
"""

# keep the adjusted close prices only:
df = df.loc[:, ['Adj. Close']]
df.rename(columns={'Adj. Close':'adj_close'}, inplace=True)

#Calculate the simple and log returns using the adjusted close prices:
df['simple_rtn'] = df.adj_close.pct_change()
df['log_rtn'] = np.log(df.adj_close/df.adj_close.shift(1))

import cufflinks as cf
from plotly.offline import iplot, init_notebook_mode
init_notebook_mode()

fig, ax = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
df.adj_close.plot(ax=ax[0])
ax[0].set(title = 'Crude Oil time series', ylabel = 'Stock price ($)')
df.simple_rtn.plot(ax=ax[1])
ax[1].set(ylabel = 'Simple returns (%)')
df.log_rtn.plot(ax=ax[2])
ax[2].set(xlabel = 'Date', ylabel = 'Log returns (%)')
plt.show()

pip install chart_studio

df['Adj. Close'].plot(title='NYMEX WTI Crude Oil time series', 
                      figsize=(14,5))
plt.show()

"""In the 3σ approach, for each time point, we calculated the moving average (μ) and standard deviation (σ) using the last 21 days (not including that day). We used 21 as this is the average number of trading days in a month, and we work with daily data."""

#Calculate the rolling mean and standard deviation:
df_rolling = df[['simple_rtn']].rolling(window=21) .agg(['mean', 'std'])
df_rolling.columns = df_rolling.columns.droplevel()

#Join the rolling metrics to the original data:
df_outliers = df.join(df_rolling)

#Define a function for detecting outliers:
def indentify_outliers(row, n_sigmas=3):
  x = row['simple_rtn']
  mu = row['mean']
  sigma = row['std']
  if (x > mu + 3 * sigma) | (x < mu - 3 * sigma):
    return 1
  else:
    return 0

#Identify the outliers and extract their values for later use:
df_outliers['outlier'] = df_outliers.apply(indentify_outliers,axis=1)
outliers = df_outliers.loc[df_outliers['outlier'] == 1,['simple_rtn']]

#Plot the results:
fig, ax = plt.subplots()
ax.plot(df_outliers.index, df_outliers.simple_rtn, color='gray', label='Normal')
ax.scatter(outliers.index, outliers.simple_rtn, color='red', label='Anomaly')
ax.set_title("Crude Oil stock returns")
ax.legend(loc='lower right')
plt.show()

"""One thing to notice is that when there are two large returns in the vicinity, the algorithm identifies the first one as an outlier and the second one as a regular observation. This might be due to the fact that the first outlier enters the rolling window and affects the moving average/standard deviation.

We should also be aware of the so-called ghost effect/feature. When a
single outlier enters the rolling window, it inflates the values of the rolling
statistics for as long as it is in the window.

### Non-Gaussian distribution of returns
Run the following steps to investigate the existence of this first fact by plotting the histogram of returns and a Q-Q plot.
1. Calculate the normal Probability Density Function (PDF) using the mean and
standard deviation of the observed returns:
"""

import scipy.stats as scs
import statsmodels.api as sm
import statsmodels.tsa.api as smt

r_range = np.linspace(min(df['log_rtn'].dropna()), max(df['log_rtn'].dropna()), num=1000)
mu = df['log_rtn'].dropna().mean()
sigma = df['log_rtn'].dropna().std()
norm_pdf = scs.norm.pdf(r_range, loc=mu, scale=sigma)

#Plot the histogram and the Q-Q plot:
fig, ax = plt.subplots(1, 2, figsize=(16, 8))
# histogram
sns.distplot(df['log_rtn'].dropna(), kde=False, norm_hist=True, ax=ax[0])
ax[0].set_title('Distribution of Crude Oil returns', fontsize=16)
ax[0].plot(r_range, norm_pdf, 'g', lw=2, label=f'N({mu:.2f}, {sigma**2:.4f})')
ax[0].legend(loc='upper left');
# Q-Q plot
qq = sm.qqplot(df['log_rtn'].dropna().values, line='s', ax=ax[1])
ax[1].set_title('Q-Q plot', fontsize = 16)
plt.show()

"""- Negative skewness: The left tail of the distribution is longer, while the mass of the distribution is concentrated on the right side of the distribution.
- Excess kurtosis: Fat-tailed and peaked distribution.

The second point is easier to observe on our plot, as there is a clear peak over the PDF and we see more mass in the tails.

## QQ plot
the empirical distribution is Normal, then the vast majority of the points will lie on the red line. However, we see that this is not the case, as points on the left side of the plot are more negative (that is, lower empirical quantiles are smaller) than expected in the case of the Gaussian distribution, as
indicated by the line. This means that the left tail of the returns distribution is heavier than that of the Gaussian distribution. Analogical conclusions can be drawn about the right tail, which is heavier than under normality.
"""

df['log_rtn'].describe()

import scipy
print("kurtosis:", scipy.stats.kurtosis(df['log_rtn'].dropna(),bias=False))
print("skewness:", scipy.stats.skew(df['log_rtn'].dropna(),bias=False))
print("JB:", scipy.stats.jarque_bera(df['log_rtn'].dropna()))

"""By looking at the metrics such as the mean, standard deviation, skewness, and
kurtosis we can infer that they deviate from what we would expect under
normality. Additionally, the Jarque-Bera normality test gives us reason to reject the null hypothesis stating that the distribution is normal at the 99% confidence level.
- Negative skewness (third moment): Large negative returns occur more
frequently than large positive ones.
- Excess kurtosis (fourth moment) : Large (and small) returns occur more often
than expected.

### Absence of autocorrelation in returns
"""

N_LAGS = 50
SIGNIFICANCE_LEVEL = 0.05
acf = smt.graphics.plot_acf(df['log_rtn'].dropna(),
                            lags=N_LAGS, alpha=SIGNIFICANCE_LEVEL)

"""Only a few values lie outside the confidence interval (we do not look at lag 0) and can be considered statistically significant. We can assume that we have verified that there is no autocorrelation in the log returns series.

### Small and decreasing autocorrelation in squared/absolute returns
Investigate this fourth fact by creating the ACF plots of squared and absolute returns.
"""

fig, ax = plt.subplots(2, 1, figsize=(12, 10))
smt.graphics.plot_acf(df['log_rtn'].dropna() ** 2, lags=N_LAGS,
                      alpha=SIGNIFICANCE_LEVEL, ax = ax[0])
ax[0].set(title='Autocorrelation Plots', ylabel='Squared Returns')
smt.graphics.plot_acf(np.abs(df['log_rtn'].dropna()), lags=N_LAGS,
                      alpha=SIGNIFICANCE_LEVEL, ax = ax[1])
ax[1].set(ylabel='Absolute Returns',xlabel='Lag')
plt.show()

# Calculate volatility measures as rolling standard deviations:
df['moving_std_252'] = df[['log_rtn']].dropna().rolling(window=252).std()
df['moving_std_21'] = df[['log_rtn']].dropna().rolling(window=21).std()

fig, ax = plt.subplots(3, 1, figsize=(18, 15), sharex=True)
df.adj_close.plot(ax=ax[0])
ax[0].set(title='Crude Oil time series', ylabel='Stock price ($)')
df['log_rtn'].dropna().plot(ax=ax[1])
ax[1].set(ylabel='Log returns (%)')
df.moving_std_252.plot(ax=ax[2], color='r', label='Moving Volatility 252d')
df.moving_std_21.plot(ax=ax[2], color='g',label='Moving Volatility 21d')
ax[2].set(ylabel='Moving Volatility', xlabel='Date')
ax[2].legend()
plt.show()

"""This fact states that most measures of asset's volatility are negatively correlated with its returns, and we can indeed observe a pattern of increased volatility when the prices go down and decreased volatility when they are rising.

We used the moving standard deviation (calculated using the rolling method of a pandas DataFrame) as a measure of historical volatility. We used windows of 21 and 252 days, which correspond to one month and one year of trading data.
"""

pip install backtrader

from datetime import datetime
import backtrader as bt

data = bt.feeds.YahooFinanceData(dataname='CL=F',fromdate=datetime(2019, 1, 1),
                                 todate=datetime(2019, 12, 31))

#Define a class representing the trading strategy:
class SmaSignal(bt.Signal):
  params = (('period', 20), )
  def __init__(self):
    self.lines.signal = self.data 
    bt.ind.SMA(period=self.p.period)

cerebro = bt.Cerebro(stdstats = False)
cerebro.adddata(data)
cerebro.broker.setcash(1000.0)
cerebro.add_signal(bt.SIGNAL_LONG, SmaSignal)
cerebro.addobserver(bt.observers.BuySell)
cerebro.addobserver(bt.observers.Value)

#Run the backtest:
print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
cerebro.run()
print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')

#Plot the results:
cerebro.plot(iplot=True, volume=False)

WINDOW_SIZE = 252
df['rolling_mean'] = df['Adj. Close'].rolling(window=WINDOW_SIZE).mean()
df['rolling_std'] = df['Adj. Close'].rolling(window=WINDOW_SIZE).std()

data = df[['Adj. Close', 'rolling_mean', 'rolling_std']]

data.plot(title='WTI Price', figsize=(14,5))
plt.show()

data.info()

from statsmodels.tsa.seasonal import seasonal_decompose
plt.rc('figure',figsize=(14,6))
plt.rc('font',size=13)

result = seasonal_decompose(data['Adj. Close'],freq=252, 
                            model='multiplicative')
plt.figure(figsize=(14,5))
result.plot()
plt.show()

"""In the decomposition plot, we can see the extracted component series: trend,
seasonal, and random (residual). To evaluate whether the decomposition makes
sense, we can look at the random component. If there is no discernible pattern (in other words, the random component is indeed random), then the fit makes sense.

For example, if we would have applied the additive model, there would be an
increasing pattern in the residuals over time. In this case, it looks like the variance in the residuals is slightly higher in the second half of the dataset.
"""

plt.rc('figure',figsize=(14,6))
plt.rc('font',size=13)


result = seasonal_decompose(data['Adj. Close'],freq=252, 
                            model='additive')
result.plot()
plt.show()

from fbprophet import Prophet

pip install stldecompose

from stldecompose import decompose, forecast
stl = decompose(data['Adj. Close'])
stl.plot()
plt.show()

df.tail()

DF = df[['Adj. Close']].copy()
DF.reset_index(drop=False, inplace=True)
DF.rename(columns={'Date': 'ds', 'Adj. Close': 'y'}, inplace=True)
DF.tail()

#Split the series into the training and test sets:
train_indices = DF.ds.apply(lambda x: x.year) < 2017
X_train = DF.loc[train_indices].dropna()
X_test = DF.loc[~train_indices].reset_index(drop=True)

print(X_train.shape, X_test.shape)

X_test.tail()

#Create the instance of the model and fit it to the data:
model = Prophet(seasonality_mode='additive')
model.add_seasonality(name='monthly', period=21, fourier_order=5)
model.fit(X_train)

future = model.make_future_dataframe(periods=252)
pred = model.predict(future)
model.plot(pred)
plt.show()

"""The black dots are the actual observations of the oil price. The blue line
representing the fit does not match the observations exactly, as the model
smooths out the noise in the data (also reducing the chance of overfitting). An
important feature is that Prophet quantifies uncertainty, which is represented by the blue intervals around the fitted line.
"""

#Inspect the decomposition of the time series:
model.plot_components(pred)
plt.show()

"""Upon closer inspection, we can see that the overall trend is increasing and that the oil price seems to be higher during the beginning and the end of the year, with a dip in the summer. On the monthly level, there is some movement, but the scale is much smaller than in the case of the yearly pattern. There is not a lot of movement in the weekly chart (we do not look at weekends as there are no prices for weekends), which makes sense because, with a decrease in the time scale, the noise starts to wash out the signal. For this reason, we might disable the weekly level altogether."""

pred.tail()

selected_columns = ['ds', 'yhat_lower', 'yhat_upper', 'yhat']
pred = pred.loc[:, selected_columns].reset_index(drop=True)
X_test = X_test.merge(pred, on=['ds'], how='left')
X_test.ds = pd.to_datetime(X_test.ds)
X_test.set_index('ds', inplace=True)

X_test.tail()

"""We merged the test set with the prediction DataFrame. We used a left join, which
returns all the rows from the left table (test set) and the matched rows from the right table (prediction DataFrame) while leaving the unmatched rows empty. This way, we also kept only the dates that were in the test set (Prophet created
predictions for the next 252 days, exclusing weekends and potential holidays).
"""

X_test = X_test.assign(day_of_week = lambda x: x.index.day_name())
X_test.tail(10)

fig, ax = plt.subplots(1, 1)
ax = sns.lineplot(data=X_test[['y', 'yhat_lower', 'yhat_upper','yhat']])
ax.fill_between(X_test.index,X_test.yhat_lower, X_test.yhat_upper, alpha=0.3)
ax.set(title='NYMEX WTI Crude Oil futures (CL) - actual vs. predicted', xlabel='Date', ylabel='Oil Price ($)')
plt.show()

"""From the preceding plot, we can see that Prophet accurately (at least visually)
predicted the price of oil over 2017-2018. It was only over the first two months that the observed prices were outside of the confidence interval.
"""

import statsmodels.api as sm
acf = pd.DataFrame(sm.tsa.stattools.acf(df['Adj. Close']), columns=['ACF'])
fig = acf[1:].plot(kind='bar', title='Autocorrelations')

from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller, kpss

x = df['Adj. Close'].values

adf = adfuller(x)
print('ADF Statistic: %f' % adf[0])
print('p-value: %f' % adf[1])
print('Critical Values:')
for key, value in adf[4].items():
	print('\t%s: %.3f' % (key, value))

pip install arch

from arch.unitroot import ADF
adf = ADF(df['Adj. Close'])
print(adf.summary().as_text())

from arch.unitroot import KPSS

kpss = KPSS(df['Adj. Close'])
print(kpss.summary().as_text())

N_LAGS = 40
SIGNIFICANCE_LEVEL = 0.05
fig, ax = plt.subplots(2, 1)
plot_acf(df['Adj. Close'], ax=ax[0], lags=N_LAGS, alpha=SIGNIFICANCE_LEVEL)
plot_pacf(df['Adj. Close'], ax=ax[1], lags=N_LAGS, alpha=SIGNIFICANCE_LEVEL)
plt.tight_layout()
plt.show()

"""In the ACF plot, we can see that there are significant autocorrelations (above the 95% confidence interval, corresponding to the selected 5% significance level). There are also some significant autocorrelations at lags 1 and 4 in the PACF plot."""

WINDOW = 12
selected_columns = ['price_log', 'rolling_mean_log','rolling_std_log']
df['price_log'] = np.log(df['Adj. Close'])
df['rolling_mean_log'] = df.price_log.rolling(window=WINDOW).mean()
df['rolling_std_log'] = df.price_log.rolling(window=WINDOW).std()
df[selected_columns].plot(title='Oil Price (logged)')
plt.show()

"""From the preceding plot, we can see that the log transformation did its job, that is,
it made the exponential trend linear.
"""

N_LAGS = 40
SIGNIFICANCE_LEVEL = 0.05
fig, ax = plt.subplots(2, 1)
plot_acf(df['price_log'], ax=ax[0], lags=N_LAGS, alpha=SIGNIFICANCE_LEVEL)
plot_pacf(df['price_log'], ax=ax[1], lags=N_LAGS, alpha=SIGNIFICANCE_LEVEL)
plt.tight_layout()
plt.show()

adf = ADF(df['price_log'])
print(adf.summary().as_text())

kpss = KPSS(df['price_log'])
print(kpss.summary().as_text())

"""After inspecting the results of the statistical tests and the ACF/PACF plots, we can conclude that a natural algorithm were not enough to make the
gold prices stationary.
"""

selected_columns = ['price_log_diff','roll_mean_log_diff','roll_std_log_diff']
df['price_log_diff'] = df.price_log.diff(1)
df['roll_mean_log_diff'] = df.price_log_diff.rolling(WINDOW).mean()
df['roll_std_log_diff'] = df.price_log_diff.rolling(WINDOW).std()
df[selected_columns].plot(title='Oil Price (1st differences)')
plt.show()

"""The transformed gold prices make the impression of being stationary – the series
oscillates around 0 with more or less constant variance. At least there is no visible trend.
"""

adf = ADF(df['price_log_diff'].dropna())
print(adf.summary().as_text())

kpss = KPSS(df['price_log_diff'].dropna())
print(kpss.summary().as_text())

N_LAGS = 40
SIGNIFICANCE_LEVEL = 0.05
fig, ax = plt.subplots(2, 1)
plot_acf(df['price_log_diff'].dropna(), ax=ax[0], lags=N_LAGS, alpha=SIGNIFICANCE_LEVEL)
plot_pacf(df['price_log_diff'].dropna(), ax=ax[1], lags=N_LAGS, alpha=SIGNIFICANCE_LEVEL)
plt.tight_layout()
plt.show()

"""After applying the first differences, the series became stationary at the 5%
significance level (according to both tests). In the ACF/PACF plots, we can see
that there was a significant value of the function at lag 6 and 15. This might
indicate some kind of seasonality or simply be a false signal. Using a 5%
significance level means that 5% of the values might lie outside the 95%
confidence interval – even when the underlying process does not show any
autocorrelation or partial autocorrelation.
"""

#Specify the risky asset and the time horizon:
RISKY_ASSET = 'CL=F'
MARKET_BENCHMARK = '^GSPC'
START_DATE = '2010-01-01'

df = yf.download([RISKY_ASSET, MARKET_BENCHMARK], start=START_DATE, adjusted=True, progress=False)

df.tail()

# Resample to monthly data and calculate the simple returns:
X = df['Adj Close'].rename(columns={RISKY_ASSET: 'asset', MARKET_BENCHMARK: 'market'}) \
.resample('M') \
.last() \
.pct_change() \
.dropna()

# Calculate beta using the covariance approach:
covariance = X.cov().iloc[0,1]
benchmark_variance = X.market.var()
beta = covariance / benchmark_variance
beta

#Prepare the input and estimate the CAPM as a linear regression:
y = X.pop('asset')
X = sm.add_constant(X)
model = sm.OLS(y, X).fit()
print(model.summary())

"""These results indicate that the beta (denoted as market here) is equal to 1.46,
which means that oil's returns are 46% more volatile than the market
(proxied by S&P 500). 

The value of the intercept is relatively small and statistically insignificant at the 5% significance level.
"""

df = quandl.get(dataset='WIKI/CL',
                       start_date='2000-01-01')
df

#data = df[['Adj. Close']]
#Calculate daily returns:
returns = 100 * df['Adj. Close'].pct_change().dropna()
returns.name = 'asset_returns'
returns.plot(title=f'{RISKY_ASSET} ')
plt.show()

from arch import arch_model
#Specify the ARCH model:
model = arch_model(returns, mean='Zero', vol='ARCH', p=1, o=0, q=0)

#Estimate the model and print the summary:
model_fitted = model.fit(disp='off')
print(model_fitted.summary())

#Plot the residuals and the conditional volatility:
model_fitted.plot(annualize='D')
plt.show()

"""We can observe some standardized residuals that are large (in magnitude) and
correspond to highly volatile periods.
"""

#Secify GARCH Model
model = arch_model(returns, mean='Zero', vol='GARCH', p=1, o=0,q=1)

#Estimate the model and print the summary:
model_fitted = model.fit(disp='off')
print(model_fitted.summary())

#Plot the residuals and the conditional volatility:
model_fitted.plot(annualize='D')
plt.show()

"""In the plots shown above, we can observe the effect of including the extra
component (lagged conditional volatility) into the model specification:

When using ARCH, the conditional volatility series exhibits many spikes, and
then immediately returns to the low level. In the case of GARCH, as the model
also includes lagged conditional volatility, it takes more time to return to the level observed before the spike.
"""