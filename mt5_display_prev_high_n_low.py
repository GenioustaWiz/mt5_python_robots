import MetaTrader5 as mt5
import matplotlib.pyplot as plt
import numpy as np

# Connect to MetaTrader 5 terminal
if not mt5.initialize():
    print("Failed to initialize MetaTrader 5")
    mt5.shutdown()
    exit(1)

# Get all the opened symbol pairs
symbols = mt5.symbols_get()

# Print the available symbols
print("Opened Symbol Pairs:")
for symbol in symbols:
    print(symbol.name)

# Prompt the user to select a symbol
# symbol = input("Enter the symbol you want to analyze: ")
symbol = "Volatility 75 (1s) Index"
# Get symbol and timeframe
timeframe = mt5.TIMEFRAME_M1  # Daily timeframe

# Check if symbol exists
symbol_info = mt5.symbol_info(symbol)
if symbol_info is None:
    print("Invalid symbol.")
    mt5.shutdown()
    exit(1)

# Request price history
rates = mt5.copy_rates_from(symbol, timeframe, 0, 100)  # Specify the number of bars you want to retrieve

# Check if rates data is available
if rates is None or len(rates) == 0:
    print("Failed to retrieve price history for the symbol.")
    mt5.shutdown()
    exit(1)

# Convert structured array to NumPy array
rates = np.atleast_1d(rates)

# Extract high and low prices from the rates
high_prices = [rate[2] for rate in rates]  # High prices at index 2
low_prices = [rate[3] for rate in rates]  # Low prices at index 3

# Find the highest price and its index
highest_price = max(high_prices)
highest_index = high_prices.index(highest_price)

# Find the lowest price and its index
lowest_price = min(low_prices)
lowest_index = low_prices.index(lowest_price)
# Define the timeframe names dictionary
timeframe_names = {
    mt5.TIMEFRAME_M1: "1 Minute",
    mt5.TIMEFRAME_M5: "5 Minutes",
    mt5.TIMEFRAME_M15: "15 Minutes",
    mt5.TIMEFRAME_M30: "30 Minutes",
    mt5.TIMEFRAME_H1: "1 Hour",
    mt5.TIMEFRAME_H4: "4 Hours",
    mt5.TIMEFRAME_D1: "Daily",
    mt5.TIMEFRAME_W1: "Weekly",
    mt5.TIMEFRAME_MN1: "Monthly"
}
# Plot the chart with the "previous high" and "previous low" annotations
plt.plot(high_prices)
plt.plot(low_prices)
plt.annotate("Previous High", xy=(highest_index, highest_price),
             xytext=(highest_index + 10, highest_price + 0.0005),
             arrowprops=dict(facecolor='red', shrink=0.05))
plt.annotate("Previous Low", xy=(lowest_index, lowest_price),
             xytext=(lowest_index + 10, lowest_price - 0.0005),
             arrowprops=dict(facecolor='green', shrink=0.05))
plt.title(f"{symbol} - {timeframe_names[timeframe]} Chart")
plt.xlabel("Bars")
plt.ylabel("Price")
plt.show()

# Disconnect from MetaTrader 5 terminal
mt5.shutdown()
