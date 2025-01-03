import os
import requests
import re
from flask import Flask

# Get MetaApi credentials from environment variables
API_KEY = os.getenv("META_API_KEY")
ACCOUNT_ID = os.getenv("META_API_ACCOUNT_ID")
SERVER = os.getenv("META_API_SERVER")
BASE_URL = f'https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{ACCOUNT_ID}/'
SIGNAL_URL = os.getenv("SIGNAL_URL",'https://alert.infipip.com/api/api.php?get_recent_posts&api_key=cda11v2OkqSI1rhQm37PBXKnpisMtlaDzoc4w0U6uNATgZRbJG&page=1&count=3')
# Check if environment variables are set
if not API_KEY or not ACCOUNT_ID or not SERVER:
    raise ValueError("API_KEY, ACCOUNT_ID, or SERVER is not set in environment variables")

# Function to place a trade using the new API
def place_trade(action, volume, entry, sl, tp, signal_id):
    print(f"Placing trade: Action={action}, Symbol=XAUUSD, Volume={volume}, Entry={entry}, SL={sl}, TP={tp}")
    if same_as_last_trade(action,volume,sl,tp):
        pass
        
    # Define the trade parameters (Order details)
    trade_data = {
        "actionType": "ORDER_TYPE_BUY" if action.lower() == 'buy' else "ORDER_TYPE_SELL",
        "symbol": "XAUUSDm",  # Gold against USD
        "volume": volume,  # Lot size (0.01 as requested)
        "takeProfit": tp,  # Take profit value
        "stopLoss": sl,    # Stop loss value
    }

    # Send the trade request to the API
    url = f'{BASE_URL}trade'
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

        # Check if the response indicates a successful trade
        if trade_response.get("numericCode") == 10009:  # Check for successful response
            print(f"Trade successful. Order ID: {trade_response['orderId']}")
        else:
            print(f"Error in trade: {trade_response.get('message', 'Unknown error')}")
    else:
        print(f"Error placing trade: {response.status_code} - {response.text}")

# Function to extract TP and SL using regex
def extract_tp_sl(description):
    print(f"Extracting TP/SL from description: {description}")

    # Remove HTML tags to work with plain text
    clean_description = re.sub(r'<.*?>', '', description)

    # Extract entry price, stop loss (SL), and take profits (TP) using refined regex
    #entry_match = re.search(r'@\s?(\d+)', clean_description)
    #tp_matches = re.findall(r'TP\s?(\d+)', clean_description, re.IGNORECASE)
    #sl_match = re.search(r'SL\s?(\d+)', clean_description, re.IGNORECASE)
    entry_match = re.search(r'Trade\s?(\d+)', clean_description)
    tp_matches = re.findall(r'Take Profit\s?(\d+)', clean_description, re.IGNORECASE)
    sl_match = re.search(r'Stop Loss\s?(\d+)', clean_description, re.IGNORECASE)


    
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
            #print(description)

            if ('buy' in description or 'sell' in description):
                if ("active" in description):
                    print(f"Active signal detected: {description}")
                else:
                    print(f"Signal inactive")
                    continue
                if ("btc" not in description):
                    print("Non btc signal and check enforced")
                else:
                    continue
                if ("gold" in description):
                    print("This is a gold signal but not check enforced")
                entry, tps, sl = extract_tp_sl(post['news_description'])
                nid = post['nid']
                
                if entry and tps:  # Ensure there's an entry and TP values
                    safest_tp = min(tps, key=lambda x: abs(x - entry))
                    print(f"Safest TP selected: {safest_tp}")

                    signals.append({
                        'action': 'buy' if 'buy' in description else 'sell',
                        'entry': entry,
                        'tp': safest_tp,
                        'sl': sl,
                        'nid': nid
                    })
                    break
    else:
        print("No valid signals detected.")
    return signals

# Function to fetch Forex signals and trigger trades
def fetch_signals_and_trade():
    print("Fetching Forex signals from the API...")
    api_url = SIGNAL_URL
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
                nid = signal['nid']

                print(f"Placing trade for signal: {signal}")
                place_trade(action, volume=0.01, entry=entry, sl=sl, tp=tp, signal_id=nid)
        else:
            print("No signals available for trading.")
    else:
        print(f"Error fetching API: {response.status_code} - {response.text}")

# Function to fetch and print all positions
def fetch_positions():
    print("Fetching current positions from the API...")
    url = f'{BASE_URL}positions'
    headers = {
        'Accept': 'application/json',
        'auth-token': API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        positions = response.json()
        return positions
        for position in positions:
            print(f"Position ID: {position['id']}")
            print(f"Symbol: {position['symbol']}")
            print(f"Type: {position['type']}")
            print(f"Open Price: {position['openPrice']}")
            print(f"Current Price: {position['currentPrice']}")
            print(f"Profit: {position['profit']}")
            print(f"Unrealized Profit: {position['unrealizedProfit']}")
            print(f"Realized Profit: {position['realizedProfit']}")
            print('-' * 40)
    else:
        print(f"Error fetching positions: {response.status_code} - {response.text}")
def same_as_last_trade(action, volume,sl, tp):
    time=None
    act={'buy':"ORDER_TYPE_BUY",'sell':"ORDER_TYPE_SELL"}
    try:
        action = action.lower()
        time = get_time()
        back_by_three = offset_by_days(time, 3)
        history = get_history(time, back_by_three);
        last_history = history[-1]
        print(f"comparing, {action},{volume}, {sl}, {tp}")
        print(f"with, {last_history['type']}, {last_history['volume']}, {last_history['stopLoss']}, {last_history['takeProfit']}")
        print()
        if act[action] == history['type'] and volume == float(history['volume']) and sl == history['stopLoss'] and tp == history['takeProfit']:
            return True
        print("Signal already in history")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


from datetime import datetime, timedelta

def offset_by_days(time_str, n):
    # Convert the ISO 8601 formatted time string to a datetime object
    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    # Offset the datetime object by 'n' days
    offset_dt = dt - timedelta(days=n)
    # Return the offset datetime object in ISO 8601 format
    return offset_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def get_history( t1, t2):
    print(f"Fetching history between {t2} and {t1} from the API...")
    url = f'{BASE_URL}history-orders/time/{t2}/{t1}'
    headers = {
        'Accept': 'application/json',
        'auth-token': API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        history_orders = response.json()
        return history_orders

def get_time():
    print("Fetching current time from the API...")
    url = f'{BASE_URL}server-time'
    headers = {
        'Accept': 'application/json',
        'auth-token': API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        time = response.json()
        return time['time']

# Main entry point
def run():
    print("Starting the trading script...")
    if fetch_positions() != []:
        print("A position is alreafy opened")
        return
    fetch_signals_and_trade()
    print("Script finished.")

app = Flask(__name__)

@app.route('/run-trade', methods=['GET'])
def run_trade():
    try:
        run()
        return "Trade executed successfully!", 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/time', methods=['GET'])
def time():
    time=None
    try:
        time = get_time()
        back_by_three = offset_by_days(time, 3)
        history = get_history(time, back_by_three);
        return f"Time is: {time} and history: {history}", 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/fetch-positions', methods=['GET'])
def fetch_all_positions():
    try:
        fetch_positions()
        return "Positions fetched successfully!", 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
