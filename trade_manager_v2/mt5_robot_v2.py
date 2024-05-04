import tkinter as tk
import MetaTrader5 as mt5
from datetime import datetime
import threading
import time

# Initialize MetaTrader5
mt5.initialize()

# Global dictionary to store trailing stop information for each position
trailing_stop_dict = {}

# Global dictionary to store break even activation status for each position
break_even_dict = {}

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
def set_break_even(ticket, pips):
    position = mt5.positions_get(ticket=ticket)
    if position:
        # Check if it's a buy position or sell position
        if position[0].type == mt5.ORDER_TYPE_BUY:
            stop_loss = position[0].price_open + (pips * position[0].symbol_info.point)
        elif position[0].type == mt5.ORDER_TYPE_SELL:
            stop_loss = position[0].price_open - (pips * position[0].symbol_info.point)

        # Set the stop loss level to the entry price
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": stop_loss
        }

        BE_order_result = mt5.order_send(request)
        print("BE_order_result: ", BE_order_result)
        return BE_order_result

def check_account_permissions():
    account_info = mt5.account_info()
    print("account_info: ",account_info)
    # Add any checks or operations to verify account permissions here
    # For example, check account groups or permissions assigned to the account

# Function to close a position
def close_position(ticket):
    positions = mt5.positions_get()
    print('here')
    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        type_dict = {0: 1, 1: 0}  # 0 represents buy, 1 represents sell - inverting order_type to close the position
        price_dict = {0: tick.ask, 1: tick.bid}

        # print("TICK: ", tick)
        if pos.ticket == ticket:
            # print("position", pos.ticket)
            # print("symbol", pos.symbol)
            # print("volume", pos.volume)
            # print("type", pos.type)
            # print("price", price_dict[pos.type])
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
                # "type_time": mt5.ORDER_TIME_GTC,
                # "type_filling": mt5.ORDER_FILLING_FOK,
            }

            CP_order_result = mt5.order_send(request)
            print("CP_order_result: ", CP_order_result)
            return CP_order_result
    return 'Ticket doesn"t exist'

# Main function to run in a separate thread
def run_main():
    # Read parameters from the GUI inputs
    MAX_LOSSES = float(entry_max_losses.get())
    MAX_LOSS_PER_TRADE = float(entry_max_loss_per_trade.get())
    BREAK_EVEN_PIPS = float(entry_break_even_pips.get())
    TRAILING_STOP_PIPS = float(entry_trailing_stop_pips.get())
    TRAILING_STOP_STEPS = float(entry_trailing_stop_steps.get())

    while True:
        # Get current account exposure
        exposure = get_exposure()

        # Calculate the current account losses
        account_info = mt5.account_info()
        account_losses = account_info.equity - account_info.balance

        # Check if the losses exceed the maximum allowed losses
        if account_losses > MAX_LOSSES:
            # Close all open positions
            positions = mt5.positions_get()
            for pos in positions:
                close_position(pos.ticket)

            # Exit the program
            break

        # Check if any position reached the maximum loss per trade
        positions = mt5.positions_get()
        for pos in positions:
            print("position", pos.ticket)
            print("symbol", pos.symbol)
            print("volume", pos.volume)
            print("type", pos.type)
            print("price", pos.price_open)
            if pos.type == mt5.ORDER_TYPE_BUY:
                symbol_tick = mt5.symbol_info_tick(pos.symbol)
                if symbol_tick is not None:
                    current_loss = pos.volume * (pos.price_open - symbol_tick.bid)
                    print("Buy Order", current_loss)
                    if current_loss >= MAX_LOSS_PER_TRADE:
                        close_position(pos.ticket)
            elif pos.type == mt5.ORDER_TYPE_SELL:
                symbol_tick = mt5.symbol_info_tick(pos.symbol)
                if symbol_tick is not None:
                    current_loss = pos.volume * (symbol_tick.ask - pos.price_open)
                    print("Sell Order", current_loss)
                    if current_loss >= MAX_LOSS_PER_TRADE:
                        close_position(pos.ticket)

        # Set break even for existing positions
        positions = mt5.positions_get()
        for pos in positions:
            # Check if break even is already set for the position
            if pos.sl == pos.price_open:
                continue

            # Check if the position is already trailing the stop loss
            if pos.ticket in trailing_stop_dict:
                continue

            # Check if break even is already activated for the position
            if pos.ticket in break_even_dict and break_even_dict[pos.ticket]:
                continue

            # Set break even if the running profit reaches the specified pips
            symbol_tick = mt5.symbol_info_tick(pos.symbol)
            if symbol_tick is not None:
                current_profit = pos.volume * (symbol_tick.bid - pos.price_open)
                if current_profit >= BREAK_EVEN_PIPS:
                    set_break_even(pos.ticket, BREAK_EVEN_PIPS)
                    break_even_dict[pos.ticket] = True

        # Trail stop loss for existing positions
        positions = mt5.positions_get()
        for pos in positions:
            # Check if the position is already trailing the stop loss
            if pos.ticket in trailing_stop_dict:
                trailing_stop_level = trailing_stop_dict[pos.ticket]
                symbol_tick = mt5.symbol_info_tick(pos.symbol)
                if symbol_tick is not None:
                    current_profit = pos.volume * (symbol_tick.bid - pos.price_open)
                    trailing_stop_level += TRAILING_STOP_STEPS

                    if current_profit >= trailing_stop_level - pos.price_open:
                        # Calculate the new stop loss level with trailing stop
                        new_stop_loss = trailing_stop_level
                        while new_stop_loss < symbol_tick.bid:
                            new_stop_loss += TRAILING_STOP_STEPS

                        # Set the new stop loss level
                        request = {
                            "action": mt5.TRADE_ACTION_SLTP,
                            "position": pos.ticket,
                            "sl": new_stop_loss
                        }
                        ts_order_result = mt5.order_send(request)
                        print("Trailing stop order result:", ts_order_result)
                        trailing_stop_dict[pos.ticket] = trailing_stop_level  # Update trailing stop level

        # Update GUI with current information
        label_exposure.config(text="Exposure: {:.2f}".format(exposure))
        label_account_losses.config(text="Account Losses: {:.2f}".format(account_losses))

        # Wait for the next iteration
        time.sleep(1)

# Function to start the program in a separate thread
def start_program():
    threading.Thread(target=run_main).start()
    check_account_permissions()

# Create GUI window
window = tk.Tk()
window.title("MT5 Position Manager")

# Help text
help_text = """
Enter the necessary parameters and click 'Start' to begin the program.
- Max Losses: Maximum allowed losses for the account.
- Max Loss Per Trade: Maximum loss allowed per trade.
- Break Even Pips: Pips profit required to set break even.
- Trailing Stop Pips: Pips profit required to start trailing stop.
- Trailing Stop Steps: Number of pips to trail the stop loss by.
"""

label_help = tk.Label(window, text=help_text, justify=tk.LEFT)
label_help.pack(pady=10)

# Parameter inputs
frame_params = tk.Frame(window)
frame_params.pack()

label_max_losses = tk.Label(frame_params, text="Max Losses:")
label_max_losses.grid(row=0, column=0, padx=5, pady=5)

entry_max_losses = tk.Entry(frame_params)
entry_max_losses.grid(row=0, column=1, padx=5, pady=5)

label_max_loss_per_trade = tk.Label(frame_params, text="Max Loss Per Trade:")
label_max_loss_per_trade.grid(row=1, column=0, padx=5, pady=5)

entry_max_loss_per_trade = tk.Entry(frame_params)
entry_max_loss_per_trade.grid(row=1, column=1, padx=5, pady=5)

label_break_even_pips = tk.Label(frame_params, text="Break Even Pips:")
label_break_even_pips.grid(row=2, column=0, padx=5, pady=5)

entry_break_even_pips = tk.Entry(frame_params)
entry_break_even_pips.grid(row=2, column=1, padx=5, pady=5)
entry_break_even_pips.insert(0, "1000")

label_trailing_stop_pips = tk.Label(frame_params, text="Trailing Stop Pips:")
label_trailing_stop_pips.grid(row=3, column=0, padx=5, pady=5)

entry_trailing_stop_pips = tk.Entry(frame_params)
entry_trailing_stop_pips.grid(row=3, column=1, padx=5, pady=5)

label_trailing_stop_steps = tk.Label(frame_params, text="Trailing Stop Steps:")
label_trailing_stop_steps.grid(row=4, column=0, padx=5, pady=5)

entry_trailing_stop_steps = tk.Entry(frame_params)
entry_trailing_stop_steps.grid(row=4, column=1, padx=5, pady=5)

# Start button
button_start = tk.Button(window, text="Start", command=start_program)
button_start.pack(pady=10)

# Information labels
label_exposure = tk.Label(window, text="Exposure: ")
label_exposure.pack()

label_account_losses = tk.Label(window, text="Account Losses: ")
label_account_losses.pack()

# Run the GUI window
window.mainloop()
