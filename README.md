# Trading-strategy

The prjcet used a combination of strategy to identify the prospect of Gold stock trading. The project used Fibonacci retracement, exponential moving average cross over followed by Backtest and Monte-Carlo simulation to identify the prospect of God trading in next 1 year.

Considering highly volatile and downward trend of Gold stock, project found long term investment option with minimum 200 days window or 233 as per Fibonacci number is advisable.

From Fibonacci retracement level plot, a major downtrend began in 2012. Price then bottomed in 2016 and retraced upward to 78.6% Fibonacci retracement level of the down move to 38.2%. In this case, 78.6% level would have been a good place to enter a short position with the goal of capitalizing on the continuation of the downtrend.

However, the likelihood of a reversal increases if there is a confluence of technical signals when price reaches a Fibonacci level. Besides Fibonacci levels, other indicators have used are candlestick patterns, exponential moving average line cross over, back tetsing and Monte-Carlo simulation to predict future trend. These indicators played a vita role to equate to a robust reversal signal.

EMA has helped reduce the noise on the series. Performed 50-day and 200-day moving average for support level. When the 50 daysEMA crosses above the 200 days EMA, it's a buy signal, as it indicates that the trend is shifting up. When the 50 days EMA crosses below the 200 days EMA, it's a sell signal, as it indicates that the trend is shifting down. These are calculated based on historical data, and nothing about the calculation is predictive in nature. Therefore, results using EMA can be random. Moreover, the price is swinging back and forth in this case, generating multiple trend reversal or trade signals. Therefore, used Backtest to help clarify the trend. 

Backtesting was performed with same 50 and 200 days wondow. Volatility measures are important here. However, backtesting can sometimes lead to over-optimization. The performance results tuned to the past may no longer as accurate in the future. Therefore, strategies that performed well in the past may fail to do well in the present. Past performance is not indicative of future results. 

Monte Carlo simulation was performed in the end. Here, continuous distribution applied using geometric brownian motion where the mean and the standard deviation are given and the mean represents the most probable value of the variable. It is symmetrical around the mean and is not bounded.
