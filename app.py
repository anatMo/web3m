import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch, helpers
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


# Function to get the real gas price in USD using Eth CoinGecko API
def get_real_gas_price():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd")
        response.raise_for_status()
        data = response.json()
        gas_price_usd = float(data['ethereum']['usd'])
        gas_price_wei = int(gas_price_usd * 10**9)  # Convert USD to Wei (1 ETH = 1e9 Gwei)
        return gas_price_wei, gas_price_usd
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None, None
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception occurred: {req_err}")
        return None, None
    except ValueError as json_err:
        print(f"Error parsing JSON: {json_err}")
        return None, None


# Get transaction data and save to Elasticsearch
def process_transactions(address, gas_price_wei, gas_price_usd):
    # now = int(datetime.now().timestamp())
    # print(f"now: {now}")
    # thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
    # print(f"thirty_days_ago: {thirty_days_ago}")

    # Get block numbers
    # url = f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={now}&closest=after&apikey={ETHERSCAN_API_KEY}"
    # response_now = requests.get(url).json()
    # result_now = response_now['result']
    # print(f"result now: {response_now}")
    # print(f"result now: {result_now}")

    # url = f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={thirty_days_ago}&closest=after&apikey={ETHERSCAN_API_KEY}"
    # response_30_days_ago = requests.get(url).json()
    # result_30_days_ago = response_30_days_ago['result']
    # print(f"result_30_days_ago: {result_30_days_ago}")

    # Get transactions list
    # url = f"https://api.etherscan.io/api?module=account&action=txlist&address=0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB&startblock={result_30_days_ago}&endblock={result_now}&page=1&offset=5000&sort=asc&apikey=WXAK8JUP9YUEXMTKI35IXQ62S29PRMA2WU"
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=17624712&endblock=17838644&page=1&offset=5000&sort=asc&apikey=WXAK8JUP9YUEXMTKI35IXQ62S29PRMA2WU"
    response_transactions = requests.get(url).json()
    result_transactions = response_transactions.get('result', [])
    print(f"result_transactions len : {len(result_transactions)}")

    # Calculate gas fee for each transaction and create the data to save in Elasticsearch
    data_to_save = []
    for tx in result_transactions:
        if 'gasUsed' not in tx:
            continue

        gas_used = int(tx['gasUsed'])
        gas_fee_wei = int(tx['gasPrice']) * gas_used
        gas_fee_eth = gas_fee_wei / 10 ** 18
        gas_fee_usd = round(gas_fee_eth * gas_price_usd, 4)  # Calculate gas fee in USD and round to 4 decimal places

        tx_data = {
            'blockNumber': tx['blockNumber'],
            'timeStamp': tx['timeStamp'],
            'gasFeeUSD': gas_fee_usd  # Add the gas fee in USD to the transaction data
        }

        data_to_save.append(tx_data)

    return data_to_save

def get_gas_price_usd():
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data.get('ethereum', {}).get('usd', 0.0)
    except Exception as e:
        print("Error fetching gas price:", str(e))
        return 0.0
    

def save_to_elasticsearch(data, address):
    # Index the data in Elasticsearch using bulk indexing
    actions = [
        {
            '_index': address.lower(),  # Convert the address to lowercase for the index name
            '_source': item
        }
        for item in data
    ]
    helpers.bulk(es, actions)


@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.get_json()  # Get JSON data from the request body
    if not data or 'address' not in data:
        return jsonify({'status': 'error', 'message': 'Address missing in the request data.'}), 400

    address = data['address'].strip().lower()  # Convert the address to lowercase

    # Check if the index (address) exists in Elasticsearch
    if es.indices.exists(index=address):
        # If the index exists, retrieve the data from Elasticsearch
        response = es.search(index=address, size=10000)  # Fetch 10,000 records (you can adjust this number)
        transaction_data = [hit['_source'] for hit in response['hits']['hits']]
        return jsonify({'status': 'success', 'result': transaction_data})

    # If the index does not exist, proceed to fetch data and save it
    gas_price_wei, gas_price_usd = get_real_gas_price()
    if gas_price_wei is None or gas_price_usd is None:
        return jsonify({'status': 'error', 'message': 'Failed to fetch gas price'})

    transaction_data = process_transactions(address, gas_price_wei, gas_price_usd)
    save_to_elasticsearch(transaction_data, address)
    return jsonify({'status': 'success', 'result': transaction_data})


@app.route('/delete_data', methods=['DELETE'])
def delete_data():
    index_name = request.args.get('index')
    
    if not index_name:
        return jsonify({'status': 'error', 'message': 'Index name missing in the request parameters.'}), 400

    try:
        response = es.indices.delete(index=index_name)
        return jsonify({'status': 'success', 'message': f'Data with index {index_name} has been deleted.'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to delete data with index {index_name}: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)