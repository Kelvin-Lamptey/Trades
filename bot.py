import os
import requests
import re
from flask import Flask

# Get MetaApi Credentials from environment variables
API_KEY = os.getenv("META_API_KEY")
ACCOUNT_ID = os.getenv("META_API_ACCOUNT_ID")
SERVER = os.getenv("META_API_SERVER")

# Check if the environment variables are set
if not API_KEY or not ACCOUNT_ID or not SERVER:
    raise ValueError("API_KEY, ACCOUNT_ID, or SERVER is not set in environment variables")

# MetaApi Base URL for REST API
BASE_URL = 'https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/'

# Function to place a trade using the new API
def place_trade(action, volume, entry, sl, tp):
    print(f"Placing trade: Action={action}, Symbol=XAUUSD, Volume={volume}, Entry={entry}, SL={sl}, TP={tp}")

    # Define the trade parameters (Order details)
    trade_data = {
        "actionType": "ORDER_TYPE_BUY" if action.lower() == 'buy' else "ORDER_TYPE_SELL",
        "symbol": "XAUUSD",  # Gold against USD
        "volume": volume,  # Lot size (0.01 as requested)
        "takeProfit": tp,  # Take profit value
        "stopLoss": sl,    # Stop loss value
    }

    # Send the trade request to the API
    url = f'{BASE_URL}{ACCOUNT_ID}/trade'
    headers = {
        'auth-token': API_KEY,  # Use API_KEY as the auth token in the header
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    print(f"Sending trade request to {url} with data: {trade_data}")
    response = requests.post(url, headers=headers, json=trade_data)

    if response.status_code == 200:
        print("Trade placed successfully.")
        trade_response = response.json()
        print(f"Trade response: {trade_response}")

        # Check if the response indicates a successful trade
        if trade_response.get("numericCode") == 10009:  # Check for successful response
            print(f"Trade successful. Order ID: {trade_response['orderId']}")
        else:
            print(f"Error in trade: {trade_response.get('message', 'Unknown error')}")
    else:
        print(f"Error placing trade: {response.status_code} - {response.text}")
        raise Exception(f"Error placing trade: {response.text}")

# Function to extract TP and SL using regex
def extract_tp_sl(description):
    print(f"Extracting TP/SL from description: {description}")

    # Remove HTML tags to work with plain text
    clean_description = re.sub(r'<.*?>', '', description)

    # Debug output to verify cleaned description
    print(f"Clean description: {clean_description}")

    # Extract entry price, stop loss (SL), and take profits (TP) using refined regex
    entry_match = re.search(r'@\s?(\d+)', clean_description)
    tp_matches = re.findall(r'TP\s?(\d+)', clean_description, re.IGNORECASE)
    sl_match = re.search(r'SL\s?(\d+)', clean_description, re.IGNORECASE)

    entry_price = float(entry_match.group(1)) if entry_match else None
    tps = [float(tp) for tp in tp_matches]  # Convert TPs to floats
    sl = float(sl_match.group(1)) if sl_match else None

    # Debug output to verify extracted values
    print(f"Extracted values: Entry={entry_price}, TPs={tps}, SL={sl}")
    return entry_price, tps, sl

# Function to detect signals from the Forex signals API
def detect_signals(data):
    print("Detecting signals from fetched data...")
    signals = []

    if data.get('status') == 'ok' and 'posts' in data:
        for post in data['posts']:
            description = post['news_description'].lower()

            # Detect buy/sell signals based on description
            if 'buy' in description or 'sell' in description:
                print(f"Signal detected: {description}")
                entry, tps, sl = extract_tp_sl(post['news_description'])

                if entry and tps:  # Ensure there's an entry and TP values
                    # Choose the safest TP (closest to the entry price)
                    safest_tp = min(tps, key=lambda x: abs(x - entry))
                    print(f"Safest TP selected: {safest_tp}")

                    signals.append({
                        'action': 'buy' if 'buy' in description else 'sell',
                        'entry': entry,
                        'tp': safest_tp,
                        'sl': sl
                    })
    else:
        print("No valid signals detected.")
    return signals

# Function to fetch Forex signals and trigger trades
def fetch_signals_and_trade():
    print("Fetching Forex signals from the API...")
    api_url = 'https://alert.infipip.com/api/api.php?get_recent_posts&api_key=cda11v2OkqSI1rhQm37PBXKnpisMtlaDzoc4w0U6uNATgZRbJG&page=1&count=3'
    headers = {
        'cache-control': 'max-age=0',
        'data-agent': 'Android News App',
        'user-agent': 'okhttp/4.10.0'
    }

    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        print("Signals fetched successfully.")
        data = response.json()
        signals = detect_signals(data)

        if signals:
            for signal in signals:
                action = signal['action']
                entry = signal['entry']
                sl = signal['sl']
                tp = signal['tp']

                # Place the trade on the new MetaApi endpoint using the updated API
                print(f"Placing trade for signal: {signal}")
                result = place_trade(action, volume=0.01, entry=entry, sl=sl, tp=tp)
                print(f"Trade result: {result}")
        else:
            print("No signals available for trading.")
    else:
        print(f"Error fetching API: {response.status_code} - {response.text}")

# Main entry point
def run():
    print("Starting the trading script...")
    fetch_signals_and_trade()
    print("Script finished.")

app = Flask(__name__)

@app.route('/run-trade', methods=['GET'])
def run_trade():
    try:
        # Example: replace with your script logic
        run()
        return "Trade executed successfully!", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)