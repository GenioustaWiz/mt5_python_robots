import tkinter as tk
import MetaTrader5 as mt5
from datetime import datetime
import threading
import time


# Connect to MetaTrader 5 terminal
if not mt5.initialize():
    print("Failed to initialize MetaTrader 5")
    mt5.shutdown()
    exit(1)

# Get all the opened symbol pairs
symbols = mt5.symbols_get()

# Print the available symbols
print("Opened Symbol Pairs:")
if symbols:
    # print(symbol.name)
    print("Symbols Available',.....................")

# Function to calculate account exposure
def get_exposure():
    positions = mt5.positions_get()
    exposure = 0.0

    for pos in positions:
        if pos.type == mt5.ORDER_TYPE_BUY:
            exposure += pos.volume
        elif pos.type == mt5.ORDER_TYPE_SELL:
            exposure -= pos.volume

    return exposure

# Function to set break even for a position
def set_break_even(ticket):
    position = mt5.positions_get(ticket=ticket)
    if position:
        # Check if it's a buy position or sell position
        if position[0].type == mt5.ORDER_TYPE_BUY:
            stop_loss = position[0].price_open
        elif position[0].type == mt5.ORDER_TYPE_SELL:
            stop_loss = position[0].price_open

        # Set the stop loss level to the entry price
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": stop_loss
        }

        BE_order_result = mt5.order_send(request)
        print("BE_order_result: ", BE_order_result)
        return BE_order_result

# Function to close a position
def close_position(ticket):
    positions = mt5.positions_get()

    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        type_dict = {0: 1, 1: 0}  # 0 represents buy, 1 represents sell - inverting order_type to close the position
        price_dict = {0: tick.ask, 1: tick.bid}

        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": type_dict[pos.type],
                "price": price_dict[pos.type],
                "magic": 0,
                "deviation": 0,
                "comment": "python close order",
            }

            CP_order_result = mt5.order_send(request)
            print("CP_order_result: ", CP_order_result)
            return CP_order_result
    return 'Ticket doesn"t exist'

# Function to calculate moving average
def calculate_ma(symbol, period, shift, method, apply_to):
    ma = mt5.iMA(symbol, 0, period, shift, method, apply_to)
    return ma

# Function to check if MA indicator one crosses MA indicator two
def check_crossing(symbol, period1, shift1, method1, apply_to1, period2, shift2, method2, apply_to2):
    ma1 = calculate_ma(symbol, period1, shift1, method1, apply_to1)
    ma2 = calculate_ma(symbol, period2, shift2, method2, apply_to2)

    if ma1[-2] < ma2[-2] and ma1[-1] > ma2[-1]:
        return 'buy'
    elif ma1[-2] > ma2[-2] and ma1[-1] < ma2[-1]:
        return 'sell'
    else:
        return None

# Main function to run in a separate thread
def run_main():
    # Read parameters from the GUI inputs
    period1 = float(entry_period1.get())
    shift1 = float(entry_shift1.get())
    method1 = method_choices1.get()
    apply_to1 = apply_to_choices1.get()
    period2 = float(entry_period2.get())
    shift2 = float(entry_shift2.get())
    method2 = method_choices2.get()
    apply_to2 = apply_to_choices2.get()
    stop_loss = float(entry_stop_loss.get())
    take_profit = float(entry_take_profit.get())
    trailing_stop_loss = float(entry_trailing_stop_loss.get())
    trailing_step = float(entry_trailing_step.get())
    lot_size = float(entry_lot_size.get())
    # Select the symbol based on the user's choice
    symbol = symbol_choices.get()

    while True:
        # Check for crossing of moving averages
        crossing = check_crossing(symbol, period1, shift1, method1, apply_to1, period2, shift2, method2, apply_to2)
        # Calculate the current account losses
        account_info = mt5.account_info()
        account_profits = account_info.equity - account_info.balance


        if crossing == 'buy':
            # Close any existing sell positions
            positions = mt5.positions_get(symbol=symbol)
            for pos in positions:
                if pos.type == mt5.ORDER_TYPE_SELL:
                    close_position(pos.ticket)

            # Open a buy position
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(symbol).ask,
                "sl": mt5.symbol_info_tick(symbol).ask - stop_loss,
                "tp": mt5.symbol_info_tick(symbol).ask + take_profit,
                "deviation": 0,
                "magic": 0,
                "comment": "Buy Order",
                # Add any additional parameters as required
            }

            buy_order_result = mt5.order_send(request)
            print("Buy Order Result: ", buy_order_result)

        elif crossing == 'sell':
            # Close any existing buy positions
            positions = mt5.positions_get(symbol=symbol)
            for pos in positions:
                if pos.type == mt5.ORDER_TYPE_BUY:
                    close_position(pos.ticket)

            # Open a sell position
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_SELL,
                "price": mt5.symbol_info_tick(symbol).bid,
                "sl": mt5.symbol_info_tick(symbol).bid + stop_loss,
                "tp": mt5.symbol_info_tick(symbol).bid - take_profit,
                "deviation": 0,
                "magic": 0,
                "comment": "Sell Order",
                # Add any additional parameters as required
            }

            sell_order_result = mt5.order_send(request)
            print("Sell Order Result: ", sell_order_result)

        # Check for trailing stop loss
        positions = mt5.positions_get(symbol=symbol)
        for pos in positions:
            if pos.type == mt5.ORDER_TYPE_BUY and trailing_stop_loss > 0.0:
                stop_loss_level = pos.price_open + trailing_stop_loss
                if mt5.symbol_info_tick(symbol).bid > stop_loss_level:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": stop_loss_level,
                        "tp": pos.tp,
                    }

                    trail_sl_result = mt5.order_send(request)
                    print("Trail SL Result: ", trail_sl_result)

            elif pos.type == mt5.ORDER_TYPE_SELL and trailing_stop_loss > 0.0:
                stop_loss_level = pos.price_open - trailing_stop_loss
                if mt5.symbol_info_tick(symbol).ask < stop_loss_level:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": stop_loss_level,
                        "tp": pos.tp,
                    }

                    trail_sl_result = mt5.order_send(request)
                    print("Trail SL Result: ", trail_sl_result)

        # Update GUI with current information
        label_exposure.config(text="Exposure: {:.2f}".format(get_exposure()))
        label_account_losses.config(text="Current Profit: {:.2f}".format(account_profits))

        # Wait for the next iteration
        time.sleep(1)

# Function to start the program in a separate thread
def start_program():
    threading.Thread(target=run_main).start()

# Create GUI window
window = tk.Tk()
window.title("MT5 Robot")

# Parameter inputs
frame_params = tk.Frame(window)
frame_params.pack()

# Indicator One parameters
label_indicator1 = tk.Label(frame_params, text="Indicator One")
label_indicator1.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

label_period1 = tk.Label(frame_params, text="Period:")
label_period1.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

entry_period1 = tk.Entry(frame_params)
entry_period1.grid(row=1, column=1, padx=5, pady=5)
entry_period1.insert(tk.END, "10")

label_shift1 = tk.Label(frame_params, text="Shift:")
label_shift1.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

entry_shift1 = tk.Entry(frame_params)
entry_shift1.grid(row=2, column=1, padx=5, pady=5)
entry_shift1.insert(tk.END, "-10")

label_method1 = tk.Label(frame_params, text="Method:")
label_method1.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)

method_choices1 = tk.StringVar(window)
method_choices1.set("Exponential")  # Set the default choice
method_dropdown1 = tk.OptionMenu(frame_params, method_choices1, "Simple", "Exponential", "Smoothed", "Linear Weighted")
method_dropdown1.grid(row=3, column=1, padx=5, pady=5)

label_apply_to1 = tk.Label(frame_params, text="Apply To:")
label_apply_to1.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)

apply_to_choices1 = tk.StringVar(window)
apply_to_choices1.set("Typical Price (HLC/3)")  # Set the default choice
apply_to_dropdown1 = tk.OptionMenu(frame_params, apply_to_choices1, "Close", "Open", "High", "Low", "Median Price (HL/2)", "Typical Price (HLC/3)", "Weighted Close (HLCC/4)")
apply_to_dropdown1.grid(row=4, column=1, padx=5, pady=5)

# Indicator Two parameters
label_indicator2 = tk.Label(frame_params, text="Indicator Two")
label_indicator2.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

label_period2 = tk.Label(frame_params, text="Period:")
label_period2.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

entry_period2 = tk.Entry(frame_params)
entry_period2.grid(row=1, column=3, padx=5, pady=5)
entry_period2.insert(tk.END, "300")

label_shift2 = tk.Label(frame_params, text="Shift:")
label_shift2.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)

entry_shift2 = tk.Entry(frame_params)
entry_shift2.grid(row=2, column=3, padx=5, pady=5)
entry_shift2.insert(tk.END, "0")

label_method2 = tk.Label(frame_params, text="Method:")
label_method2.grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)

method_choices2 = tk.StringVar(window)
method_choices2.set("Exponential")  # Set the default choice
method_dropdown2 = tk.OptionMenu(frame_params, method_choices2, "Simple", "Exponential", "Smoothed", "Linear Weighted")
method_dropdown2.grid(row=3, column=3, padx=5, pady=5)

label_apply_to2 = tk.Label(frame_params, text="Apply To:")
label_apply_to2.grid(row=4, column=2, padx=5, pady=5, sticky=tk.W)

apply_to_choices2 = tk.StringVar(window)
apply_to_choices2.set("Previous Indicator's Data")  # Set the default choice
apply_to_dropdown2 = tk.OptionMenu(frame_params, apply_to_choices2, "Close", "Open", "High", "Low", "Median Price (HL/2)", "Typical Price (HLC/3)", "Weighted Close (HLCC/4)", "Previous Indicator's Data")
apply_to_dropdown2.grid(row=4, column=3, padx=5, pady=5)

# Stop Loss and Take Profit parameters
label_stop_loss = tk.Label(frame_params, text="Stop Loss (pips):")
label_stop_loss.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)

entry_stop_loss = tk.Entry(frame_params)
entry_stop_loss.grid(row=5, column=1, padx=5, pady=5)
entry_stop_loss.insert(tk.END, "0")

label_take_profit = tk.Label(frame_params, text="Take Profit (pips):")
label_take_profit.grid(row=5, column=2, padx=5, pady=5, sticky=tk.W)

entry_take_profit = tk.Entry(frame_params)
entry_take_profit.grid(row=5, column=3, padx=5, pady=5)
entry_take_profit.insert(tk.END, "0")

# Trailing Stop Loss parameters
label_trailing_stop_loss = tk.Label(frame_params, text="Trailing Stop Loss (pips):")
label_trailing_stop_loss.grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)

entry_trailing_stop_loss = tk.Entry(frame_params)
entry_trailing_stop_loss.grid(row=6, column=1, padx=5, pady=5)
entry_trailing_stop_loss.insert(tk.END, "0")

label_trailing_step = tk.Label(frame_params, text="Trailing Step (pips):")
label_trailing_step.grid(row=6, column=2, padx=5, pady=5, sticky=tk.W)

entry_trailing_step = tk.Entry(frame_params)
entry_trailing_step.grid(row=6, column=3, padx=5, pady=5)
entry_trailing_step.insert(tk.END, "0")

# Symbol selection
label_symbol = tk.Label(frame_params, text="Symbol:")
label_symbol.grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)

symbol_choices = tk.StringVar(window)
symbol_choices.set(symbols[0].name)  # Set the default choice
symbol_dropdown = tk.OptionMenu(frame_params, symbol_choices, *[symbol.name for symbol in symbols])
symbol_dropdown.grid(row=7, column=1, padx=5, pady=5, columnspan=3)

label_lot_size = tk.Label(frame_params, text="Lot Size:")
label_lot_size.grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)

entry_lot_size = tk.Entry(frame_params)
entry_lot_size.grid(row=8, column=1, padx=5, pady=5, columnspan=3)
entry_lot_size.insert(tk.END, "0.01")
# Start button
button_start = tk.Button(window, text="Start", command=start_program)
button_start.pack(pady=10)

# Information labels
label_exposure = tk.Label(window, text="Exposure: ")
label_exposure.pack()
label_account_losses = tk.Label(window, text="Current Profit: ")
label_account_losses.pack()

# Run the GUI window
window.mainloop()
