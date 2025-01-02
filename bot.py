import os
import requests
import re
import redis
from flask import Flask
import json

# Get MetaApi and Redis credentials from environment variables
API_KEY = os.getenv("META_API_KEY")
ACCOUNT_ID = os.getenv("META_API_ACCOUNT_ID")
SERVER = os.getenv("META_API_SERVER")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Check if the environment variables are set
if not API_KEY or not ACCOUNT_ID or not SERVER:
    raise ValueError("API_KEY, ACCOUNT_ID, or SERVER is not set in environment variables")

# Initialize Redis connection
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Function to place a trade using the new API
def place_trade(action, volume, entry, sl, tp, signal_id):
    # Check if the signal_id has already been traded (using Redis)
    if redis_client.get(f"trade:{signal_id}"):
        print("Already traded signal")
        return

    print(f"Placing trade: Action={action}, Symbol=XAUUSD, Volume={volume}, Entry={entry}, SL={sl}, TP={tp}")

    # Define the trade parameters (Order details)
    trade_data = {
        "actionType": "ORDER_TYPE_BUY" if action.lower() == 'buy' else "ORDER_TYPE_SELL",
        "symbol": "XAUUSDm",  # Gold against USD
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

        # Store the trade details in Redis (convert data to JSON)
        redis_client.set(f"trade:{signal_id}", json.dumps({
            "action": action,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "status": "success"
        }))
        print(f"Trade response: {trade_response}")

        # Check if the response indicates a successful trade
        if trade_response.get("numericCode") == 10009:  # Check for successful response
            print(f"Trade successful. Order ID: {trade_response['orderId']}")
        else:
            print(f"Error in trade: {trade_response.get('message', 'Unknown error')}")
    else:
        print(f"Error placing trade: {response.status_code} - {response.text}")
        # Log the error in Redis
        redis_client.set(f"trade:{signal_id}", json.dumps({
            "action": action,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "status": "failed"
        }))

# Function to extract TP and SL using regex
def extract_tp_sl(description):
    print(f"Extracting TP/SL from description: {description}")

    # Remove HTML tags to work with plain text
    clean_description = re.sub(r'<.*?>', '', description)

    # Extract entry price, stop loss (SL), and take profits (TP) using refined regex
    entry_match = re.search(r'@\s?(\d+)', clean_description)
    tp_matches = re.findall(r'TP\s?(\d+)', clean_description, re.IGNORECASE)
    sl_match = re.search(r'SL\s?(\d+)', clean_description, re.IGNORECASE)

    entry_price = float(entry_match.group(1)) if entry_match else None
    tps = [float(tp) for tp in tp_matches]  # Convert TPs to floats
    sl = float(sl_match.group(1)) if sl_match else None

    print(f"Extracted values: Entry={entry_price}, TPs={tps}, SL={sl}")
    return entry_price, tps, sl

# Function to detect signals from the Forex signals API
def detect_signals(data):
    print("Detecting signals from fetched data...")
    signals = []

    if data.get('status') == 'ok' and 'posts' in data:
        for post in data['posts']:
            description = post['news_description'].lower()

            if ('buy' in description or 'sell' in description) and "active" in description:
                print(f"Signal detected: {description}")
               
