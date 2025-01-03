import os
import requests
import re
from flask import Flask
from requests_html import HTMLSession

# Get MetaApi and Redis credentials from environment variables
API_KEY = os.getenv("META_API_KEY")
ACCOUNT_ID = os.getenv("META_API_ACCOUNT_ID")
SERVER = os.getenv("META_API_SERVER")

# Check if environment variables are set
if not API_KEY or not ACCOUNT_ID or not SERVER:
    raise ValueError("API_KEY, ACCOUNT_ID, or SERVER is not set in environment variables")

# Function to visit the URL using requests-html and handle cookies
def visit_trades_info():
    print("Visiting trades.infy.uk/tradesinfo.php using requests-html with cookies...")

    # Create a session to handle cookies and other session-based settings
    session = HTMLSession()

    try:
        # Send a GET request to the URL
        response = session.get('http://trades.infy.uk/tradesinfo.php')

        # Allow the page to load fully (if JavaScript rendering is required)
        response.html.render()

        # Print the page source (HTML response)
        page_source = response.text
        print("Page Source:")
        print(page_source)

        # Optionally, you can access cookies here:
        print("Cookies received:")
        for cookie in session.cookies:
            print(cookie)

    except Exception as e:
        print(f"Error visiting the URL: {e}")
    finally:
        session.close()

# Main entry point
def run():
    print("Starting the trading script...")
    fetch_signals_and_trade()
    print("Script finished.")

app = Flask(__name__)

@app.route('/run-trade', methods=['GET'])
def run_trade():
    try:
        # Visit the URL with requests-html (handling cookies)
        visit_trades_info()
        
        # Continue with the original trade process
        #run()
        return "Trade executed successfully!", 200
    except Exception as e:
        # Log the error in Redis
        #redis_client.lpush("errors", str(e))
        print(f"Error: {str(e)}")
        return f"Error:", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
