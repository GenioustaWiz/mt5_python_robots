import MetaTrader5 as mt5
import winsound
import smtplib
from email.mime.text import MIMEText

# Connect to MetaTrader 5 terminal
if not mt5.initialize():
    print("Failed to initialize MetaTrader 5")
    exit(1)

# Get the login information from MetaTrader 5
login_info = mt5.login_get()
account_number = login_info.login
password = login_info.password

# Login to the trading account
if not mt5.login(account_number, password):
    print("Failed to login to the trading account")
    mt5.shutdown()
    exit(1)

# Define the break-even percentage and maximum losses
break_even_percentage = 0.5  # 0.5% break-even
max_losses = 1000  # Maximum allowed losses in account currency

# Get the account currency
account_info = mt5.account_info()
account_currency = account_info.currency

# Calculate the break-even amount in account currency
break_even_amount = account_info.balance * break_even_percentage / 100

# Email configuration
email_sender = "your_email@gmail.com"  # Replace with the sender's email address
email_password = "your_email_password"  # Replace with the sender's email password
email_receiver = "cm0215557@gmail.com"  # Replace with the receiver's email address

# Main trading loop
while True:
    # Get open positions
    positions = mt5.positions_get()

    for position in positions:
        # Get the symbol of the position's chart
        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info is None:
            continue

        # Get the current profit/loss of the position in account currency
        profit_loss = position.profit

        # Check if the position is in loss
        if profit_loss < 0:
            # Check if the loss has reached the break-even amount
            if abs(profit_loss) >= break_even_amount:
                # Set the break-even price as the entry price
                mt5.position_modify(position.ticket, position.price_open, sl=position.sl)

            # Check if the loss has reached the maximum allowed losses
            if abs(profit_loss) >= max_losses:
                # Close the position
                mt5.position_close(position.ticket)
                # Play sound notification
                winsound.Beep(1000, 200)  # Adjust the frequency (1000) and duration (200) as desired

                # Send email notification
                subject = f"Position Closed: {position.symbol}"
                body = f"The position for symbol {position.symbol} has reached the maximum allowed losses and has been closed."
                message = MIMEText(body)
                message["Subject"] = subject
                message["From"] = email_sender
                message["To"] = email_receiver

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(email_sender, email_password)
                    server.sendmail(email_sender, email_receiver, message.as_string())

    # Check the account balance for losses
    if account_info.profit < -max_losses:
        # Close all positions
        positions = mt5.positions_get()
        for position in positions:
            mt5.position_close(position.ticket)
            # Play sound notification
            winsound.Beep(1000, 200)  # Adjust the frequency (1000) and duration (200) as desired

            # Send email notification
            subject = f"Position Closed: {position.symbol}"
            body = f"The position for symbol {position.symbol} has reached the maximum allowed losses and has been closed."
            message = MIMEText(body)
            message["Subject"] = subject
            message["From"] = email_sender
            message["To"] = email_receiver

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(email_sender, email_password)
                server.sendmail(email_sender, email_receiver, message.as_string())

    # Wait for some time before checking positions again (e.g., 1 minute)
    mt5.sleep(60000)

# Disconnect from MetaTrader 5 terminal and shutdown
mt5.shutdown()
