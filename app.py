import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch, helpers
import utils
from constants import ES_CLOUD_ID, ES_USER, ES_PASSWORD, USERNAME, PASSWORD


app = Flask(__name__)



# Initialize Elasticsearch client
es = Elasticsearch(
    cloud_id=ES_CLOUD_ID,
    basic_auth=(ES_USER, ES_PASSWORD)
)

# Login page APIs
@app.route('/')
def login_page():
    return render_template('login.html', error=None)



@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username == USERNAME and password == PASSWORD:
        return redirect(url_for('tools_page'))
    else:
        return render_template('login.html', error='Invalid credentials.')


# Tools page APIs
@app.route('/tools')
def tools_page():
    return render_template('tools.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.get_json()  # Get JSON data from the request body
    if not data or 'address' not in data or 'selectedDay' not in data:
        return jsonify({'status': 'error', 'message': 'Address or selectedDay missing in the request data.'}), 400

    address = data['address'].strip().lower()  # Convert the address to lowercase
    selected_day_index = int(data['selectedDay'])

    # Calculate the timestamps for the last 30 days
    dates = utils.get_last_30_days()
    selected_day = dates[selected_day_index]

    # Calculate the timestamp for the selected day
    selected_day_timestamp = utils.get_timestamp(selected_day)

    # Calculate the timestamp for the day after the selected day (for range calculation)
    next_day_timestamp = utils.get_timestamp(selected_day, add_days=1)

    # Check if the index (address) exists in Elasticsearch
    if check_index_exists(address):

        # If the index exists, retrieve the data from Elasticsearch
        response = es.search(index=address, size=10000)  # Fetch up to 10,000 records
        transaction_data = [hit['_source'] for hit in response['hits']['hits']]

        # Filter the data for the selected day
        selected_day_data = utils.filter_by_timestamp(transaction_data, selected_day_timestamp, next_day_timestamp)

        # Calculate the hourly averages for the selected day
        hourly_averages = utils.calculate_hourly_average(selected_day_data)

        return jsonify({'status': 'success', 'result': selected_day_data, 'hourly_averages': hourly_averages, 'days': dates})
    else:
        # If the index does not exist, proceed to fetch data and save it
        gas_price_wei, gas_price_usd = utils.get_real_gas_price()
        if gas_price_wei is None or gas_price_usd is None:
            return jsonify({'status': 'error', 'message': 'Failed to fetch gas price'})

        transaction_data = utils.process_transactions(address, gas_price_usd)
        save_to_elasticsearch(transaction_data, address)

        # Filter the data for the selected day
        selected_day_data = utils.filter_by_timestamp(transaction_data, selected_day_timestamp, next_day_timestamp)
        hourly_averages = utils.calculate_hourly_average(selected_day_data)

        return jsonify({'status': 'success', 'result': selected_day_data, 'hourly_averages': hourly_averages, 'days': dates})

def check_index_exists(index_name):
    return es.indices.exists(index=index_name)

def save_to_elasticsearch(data, address):
    # Index the data in Elasticsearch using bulk indexing(to speed up the process)
    actions = [
        {
            '_index': address.lower(),  # Convert the address to lowercase for the index name
            '_source': item
        }
        for item in data
    ]
    helpers.bulk(es, actions)

# For testing
# @app.route('/delete_data', methods=['DELETE'])
# def delete_data():
#     index_name = request.args.get('index')
    
#     if not index_name:
#         return jsonify({'status': 'error', 'message': 'Index name missing in the request parameters.'}), 400

#     try:
#         response = es.indices.delete(index=index_name)
#         return jsonify({'status': 'success', 'message': f'Data with index {index_name} has been deleted.'}), 200
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': f'Failed to delete data with index {index_name}: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)