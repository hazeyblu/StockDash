import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout='wide')


# Load data
# noinspection PyShadowingNames
@st.cache_data
def load_data():
    momentum = pd.read_csv("N500_Momentum.csv", index_col=0, parse_dates=True, dayfirst=True)
    alpha = pd.read_csv("N500_Alpha.csv", index_col=0, parse_dates=True, dayfirst=True)
    prices = pd.read_csv("N500_Prices.csv", index_col=0, parse_dates=True, dayfirst=True)
    return momentum, alpha, prices


momentum, alpha, prices = load_data()

# Align data with alpha's index
momentum = momentum.reindex(alpha.index)
prices = prices.reindex(alpha.index)

# Sidebar controls
st.sidebar.header("Strategy Parameters")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime(alpha.index.min()))
end_date = st.sidebar.date_input("End Date", pd.to_datetime(alpha.index.max()))
trade_freq = st.sidebar.number_input("Trade Frequency (days)", min_value=1, value=5)
top_n_alpha_exclude = st.sidebar.number_input("Top N Alpha Stocks to Exclude", min_value=0, value=5)
use_alpha_filter = st.sidebar.checkbox("Apply Alpha Exclusion", value=False)
top_n_momentum = st.sidebar.number_input("Top N Momentum Stocks", min_value=1, value=10)
show_long = st.sidebar.radio("Show Performance of", ["Long", "Short"])

# Filter data based on date range
date_range = (alpha.index >= str(start_date)) & (alpha.index <= str(end_date))
momentum = momentum.loc[date_range]
alpha = alpha.loc[date_range]
prices = prices.loc[date_range]

# Generate trade signals
trade_dates = alpha.index[::trade_freq]
long_baskets = {}
short_baskets = {}
returns = pd.DataFrame(index=trade_dates)
benchmark = prices['NIFTY 500'].pct_change().reindex(trade_dates).fillna(0)

for date in trade_dates:
    if date not in alpha.index:
        continue

    # Exclude top N alpha stocks if option is selected
    if use_alpha_filter:
        excluded_stocks = alpha.loc[date].nlargest(top_n_alpha_exclude).index
        remaining_stocks = alpha.columns.difference(excluded_stocks)
    else:
        remaining_stocks = alpha.columns

    # Select top N momentum stocks from the remaining pool
    top_momentum = momentum.loc[date, remaining_stocks].nlargest(top_n_momentum).index

    long_stocks = list(top_momentum)
    short_stocks = list(set(remaining_stocks) - set(long_stocks))

    long_baskets[date] = long_stocks
    short_baskets[date] = short_stocks

    if show_long == "Long":
        returns.loc[date, "Portfolio"] = prices[long_stocks].pct_change().loc[date].mean()
    else:
        returns.loc[date, "Portfolio"] = -prices[short_stocks].pct_change().loc[date].mean()

returns["Benchmark"] = benchmark
cumulative_returns = (1+returns).cumprod() * 100


# Plot results
st.subheader("Performance Over Time")
fig, ax = plt.subplots()
ax.plot(cumulative_returns.index, cumulative_returns["Portfolio"], label="Portfolio")
ax.plot(cumulative_returns.index, cumulative_returns["Benchmark"], label="Benchmark", linestyle="--")
ax.legend()
st.pyplot(fig)

benchmarkReturn = (cumulative_returns.Benchmark.tail(1).values[0] / 100) - 1
st.text(f"Benchmark Return : {benchmarkReturn:.2%}")
portfolioReturn = (cumulative_returns.Portfolio.tail(1).values[0] / 100) - 1
st.text(f"Portfolio Return : {portfolioReturn:.2%}")

# Show basket on a chosen day
st.subheader("Stock Basket on Selected Date")
selected_date = st.selectbox("Select Date", trade_dates)
if show_long == "Long":
    st.write("Long Basket:", long_baskets.get(selected_date, []))
else:
    st.write("Short Basket:", short_baskets.get(selected_date, []))
