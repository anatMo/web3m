import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import requests

app = Flask(__name__)

# Constants
USERNAME = 'crypto_whale'
PASSWORD = 'js*gnHfcx!'
ETHERSCAN_API_KEY = 'WXAK8JUP9YUEXMTKI35IXQ62S29PRMA2WU'
COINGECKO_API_URL = 'https://api.coingecko.com/api/v3/simple/price'
COINGECKO_CURRENCY = 'usd'
ES_CLOUD_ID = 'My_deployment:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvJGVkMmJiZWRiYTQyOTQwOTBhODJmOTZjMGRmZGY3ZWUwJDZkZTIyMjA1YzE1NDQ5YjBiZDVhN2FjZjAwMDBlYzEx'
ES_USER = 'elastic'
ES_PASSWORD = 'dafyA4SGNygnhKuoJCDszz5j'

# Initialize Elasticsearch client
es = Elasticsearch(
    cloud_id=ES_CLOUD_ID,
    basic_auth=(ES_USER, ES_PASSWORD)
)


@app.route('/')
def login_page():
    return render_template('login.html', error=None)


# Login page
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username == USERNAME and password == PASSWORD:
        return redirect(url_for('tools_page'))
    else:
        return render_template('login.html', error='Invalid credentials.')


# Tools page
@app.route('/tools')
def tools_page():
    return render_template('tools.html')


# Function to get the real gas price in USD using CoinGecko API
def get_real_gas_price():
    try:
        response = requests.get(f"{COINGECKO_API_URL}?ids=ethereum&vs_currencies={COINGECKO_CURRENCY}")
        response.raise_for_status()
        data = response.json()
        return data.get('ethereum', {}).get(COINGECKO_CURRENCY)
    except requests.exceptions.RequestException as e:
        print("Error fetching gas price:", e)
        return None


# Get transaction data and save to Elasticsearch
def process_transactions(address, gas_price_wei, gas_price_usd):
    now = int(datetime.now().timestamp())
    thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())

    # Get block numbers
    url = f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={now}&closest=after&apikey={ETHERSCAN_API_KEY}"
    response_now = requests.get(url).json()
    result_now = response_now['result']

    url = f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={thirty_days_ago}&closest=after&apikey={ETHERSCAN_API_KEY}"
    response_30_days_ago = requests.get(url).json()
    result_30_days_ago = response_30_days_ago['result']

    # Get transactions list
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock={result_now}&endblock={result_30_days_ago}&page=1&offset=2000&sort=asc&apikey={ETHERSCAN_API_KEY}"
    response_transactions = requests.get(url).json()
    result_transactions = response_transactions['result']

    # Calculate gas fee for each transaction and create the data to save in Elasticsearch
    data_to_save = []
    for tx in result_transactions:
        gas_used = int(tx['gasUsed'])
        gas_fee_wei = gas_price_wei * gas_used
        gas_fee_eth = gas_fee_wei / 10 ** 18
        gas_fee_usd = round(gas_fee_eth * gas_price_usd, 4)  # Calculate gas fee in USD and round to 4 decimal places

        tx_data = {
            'blockNumber': tx['blockNumber'],
            'timeStamp': tx['timeStamp'],
            'gasFeeUSD': gas_fee_usd  # Add the gas fee in USD to the transaction data
        }

        data_to_save.append(tx_data)

    # Save the data_to_save to Elasticsearch with the index as the contract address
    # es.index(index=address.lower(), doc_type='transaction', body=json.dumps(data_to_save))

    return data_to_save


@app.route('/get_info', methods=['POST'])
def get_info():
    address = request.json.get('address')

    # Get the real gas price in USD
    gas_price_usd = get_real_gas_price()

    if gas_price_usd is None:
        return jsonify({'status': 'error', 'message': 'Failed to fetch gas price.'})

    # Get the real gas price in Wei
    gas_price_wei = int(1 / gas_price_usd * 10 ** 9)

    # Process transactions and get data to display
    transaction_data = process_transactions(address, gas_price_wei, gas_price_usd)

    return jsonify({'status': 'success', 'result': transaction_data})

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
