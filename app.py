import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from elasticsearch import Elasticsearch
import requests

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Hard-coded user and password
USERNAME = 'crypto_whale'
PASSWORD = 'js*gnHfcx!'

# Read Elasticsearch credentials from environment variables
ELASTICSEARCH_USERNAME = os.environ.get('ELASTICSEARCH_USERNAME')
ELASTICSEARCH_PASSWORD = os.environ.get('ELASTICSEARCH_PASSWORD')
ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST', 'http://localhost:9200')

# # Elasticsearch connection
# es = Elasticsearch(
#     [ELASTICSEARCH_HOST],
#     basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
# )

es = Elasticsearch(
    cloud_id="My_deployment:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvJGVkMmJiZWRiYTQyOTQwOTBhODJmOTZjMGRmZGY3ZWUwJDZkZTIyMjA1YzE1NDQ5YjBiZDVhN2FjZjAwMDBlYzEx",
    basic_auth=("elastic", "dafyA4SGNygnhKuoJCDszz5j")
)


print("connected")

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


# Save Data to Elasticsearch
@app.route('/save_data', methods=['POST'])
def save_data():
    title = request.form['title']
    content = request.form['content']

    # Prepare data to save in Elasticsearch
    data = {
        'title': title,
        'content': content,
    }

    # Index the document in Elasticsearch
    index_name = 't1'
    document_id = str(hash(title + content))  # Use a unique document ID
    print(document_id)
    es.index(index=index_name, id=document_id, document=data)

    return redirect(url_for('tools_page'))

# Retrieve Data from Elasticsearch
@app.route('/retrieve_data', methods=['GET'])
def retrieve_data():
    document_id = request.args.get('document_id')

    # Retrieve the document from Elasticsearch
    index_name = 't1'
    try:
        result = es.get(index=index_name, id=document_id)
        retrieved_data = result['_source']
        return render_template('tools.html', retrieved_data=retrieved_data)
    except Exception as e:
        # Handle errors, such as when the document with the given ID doesn't exist
        return render_template('tools.html', error='Document not found')

# # Function to connect to Elasticsearch via Kibana
# def connect_to_elasticsearch(method, path, data=None):
#     base_url = 'http://localhost:5601'  # Kibana URL
#     auth = ('your_kibana_username', 'your_kibana_password')  # Kibana credentials

#     url = f'{base_url}/api/console/proxy?method={method}&path={path}'

#     if method == 'GET':
#         response = requests.get(url, auth=auth)
#     elif method == 'POST':
#         headers = {'Content-Type': 'application/json'}
#         response = requests.post(url, headers=headers, json=data, auth=auth)
#     else:
#         # Add more HTTP methods if needed (e.g., PUT, DELETE)
#         return None

#     return response

# # Save Data to Elasticsearch via Kibana
# @app.route('/save_data', methods=['POST'])
# def save_data():
#     title = request.form['title']
#     content = request.form['content']

#     # Prepare data to save in Elasticsearch
#     data = {
#         'title': title,
#         'content': content,
#     }

#     # Index the document in Elasticsearch via Kibana
#     index_name = 't1'
#     document_id = str(hash(title + content))  # Use a unique document ID

#     response = connect_to_elasticsearch('POST', f'/{index_name}/_doc/{document_id}', data=data)

#     # Check the response status code and handle accordingly
#     if response and response.status_code == 200:
#         return redirect(url_for('tools_page'))
#     else:
#         return render_template('tools.html', error='Failed to save data.')

# # Retrieve Data from Elasticsearch via Kibana
# @app.route('/retrieve_data', methods=['GET'])
# def retrieve_data():
#     document_id = request.args.get('document_id')

#     # Retrieve the document from Elasticsearch via Kibana
#     response = connect_to_elasticsearch('GET', f'/t1/_doc/{document_id}')

#     # Check the response status code and handle accordingly
#     if response and response.status_code == 200:
#         retrieved_data = response.json()
#         return render_template('tools.html', retrieved_data=retrieved_data)
#     else:
#         return render_template('tools.html', error='Document not found')

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)