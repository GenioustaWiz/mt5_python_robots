import MetaTrader5 as mt5
import numpy as np
import time

# Connect to MT5
mt5.initialize()

# Get symbol and timeframe
symbol = "Volatility 25 Index"
timeframe = mt5.TIMEFRAME_M1

# Infinite loop
while True:
    # Request chart data
    chart_data = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)

    # Extract close prices from chart data
    close_prices = np.array([bar[4] for bar in chart_data])

    # Calculate SMA using numpy
    sma = np.mean(close_prices)

    # Print the SMA
    print("SMA:", sma)

    # Wait for some time (e.g., 1 second) before the next iteration
    time.sleep(1)

# Disconnect from MT5 (this won't be reached in the infinite loop)
mt5.shutdown()
