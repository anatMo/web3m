from datetime import datetime, timedelta
import requests
from constants import ETHERSCAN_API_KEY, PASSWORD

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
    
# Returns the nearest block number before the timestemp
def get_block_number_by_time(timestamp):
    url = f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={timestamp}&closest=before&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url).json()
    return response['result']

# Returns transaction list of specific contract address from x block number to y block number
def get_transactions_list(address, start_block, end_block):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock={start_block}&endblock={end_block}&page=1&offset=5000&sort=asc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url).json()
    return response.get('result', [])

# Get transaction data and save to Elasticsearch
def process_transactions(address, gas_price_usd):
    now = int(datetime.now().timestamp())
    print(f"now: {now}")
    thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
    print(f"thirty_days_ago: {thirty_days_ago}")

    # Get block numbers
    result_now = get_block_number_by_time(now)
    print(f"result now: {result_now}")

    result_30_days_ago = get_block_number_by_time(thirty_days_ago)
    print(f"result_30_days_ago: {result_30_days_ago}")

    # Get transactions list
    result_transactions = get_transactions_list(address, result_30_days_ago, result_now)
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

# Get real time gas fee in USD using coingecko API
def get_gas_price_usd():
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data.get('ethereum', {}).get('usd', 0.0)
    except Exception as e:
        print("Error fetching gas price:", str(e))
        return 0.0
    
def calculate_hourly_average(data):
    hourly_data = {}
    for tx in data:
        timestamp = int(tx['timeStamp'])
        hour = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:00')
        gas_fee = tx['gasFeeUSD']
        if hour not in hourly_data:
            hourly_data[hour] = []
        hourly_data[hour].append(gas_fee)

    hourly_averages = []
    for hour, fees in hourly_data.items():
        average_fee = sum(fees) / len(fees)
        hourly_averages.append([hour, round(average_fee, 4)])

    return hourly_averages

# Returns list of 30 last dates
def get_last_30_days():
    now = datetime.now()
    dates = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    return dates

def get_last_30_days():
    now = datetime.now()
    dates = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    return dates

def get_timestamp(date_string, add_days=0):
    date_obj = datetime.strptime(date_string, '%Y-%m-%d')
    return int((date_obj + timedelta(days=add_days)).timestamp())


def filter_by_timestamp(transaction_data, start_timestamp, end_timestamp):
    return [tx for tx in transaction_data if int(tx['timeStamp']) >= start_timestamp and int(tx['timeStamp']) < end_timestamp]
