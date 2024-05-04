import MetaTrader5 as mt5
import pandas as pd

# Connect to MT5
mt5.initialize()

# Get symbol and timeframe
symbol = "Volatility 25 Index"
timeframe = mt5.TIMEFRAME_M1

# Request chart data
chart_data = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)

# Create a Pandas DataFrame from the chart data
df = pd.DataFrame(chart_data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'spread', 'real_volume'])

# Calculate EMA using Pandas
ema = df['close'].ewm(span=10, adjust=False).mean()

# Print the EMA
print("EMA:", ema)

# Disconnect from MT5
mt5.shutdown()
