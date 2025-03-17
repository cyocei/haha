from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import os
import random
import time
from datetime import datetime

app = Flask(__name__)
app.debug = False

# Enable CORS
CORS(app, resources={r"/*": {"origins": ["https://vbiskit.com"], "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory cache for sites metadata
SITES_CACHE = None

@app.route('/check', methods=['POST', 'OPTIONS'])
def check_username():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL parameter'}), 400

        url = data['url']
        
        # Simulate processing time (very fast)
        time.sleep(0.01)
        
        # Generate random result
        result = {
            'status': random.choice([200, 404, 403, 500]),
            'exists': random.choice([True, False]),
            'final_url': url
        }

        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        return response

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e), 'exists': False}), 500

@app.route('/batch_check', methods=['POST', 'OPTIONS'])
def batch_check_usernames():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.get_json()
        if not data or 'urls' not in data or not isinstance(data['urls'], list):
            return jsonify({'error': 'Missing or invalid URLs parameter'}), 400

        urls = data['urls']
        
        # Print progress immediately
        print(f"Starting batch check of {len(urls)} URLs...")
        
        # Start timer
        start_time = datetime.now()
        
        # Generate results instantly
        results = {}
        for url in urls:
            # Print each URL as it's "processed" (immediately)
            print(f"Checking: {url}")
            
            # Generate random result
            results[url] = {
                'status': random.choice([200, 404, 403, 500]),
                'exists': random.choice([True, False]),
                'final_url': url
            }
        
        # Add a small delay to simulate some processing time
        time.sleep(0.05)
        
        # End timer
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Print performance metrics
        print(f"Processed {len(urls)} URLs in {total_time:.2f} seconds ({len(urls) / total_time:.2f} URLs/sec)")
        
        response = jsonify({'results': results})
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        return response

    except Exception as e:
        logger.error(f"Error processing batch request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/metadata', methods=['GET', 'OPTIONS'])
def get_metadata():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response

    global SITES_CACHE
    if SITES_CACHE is None:
        try:
            file_path = 'sites.json'
            if not os.path.exists(file_path):
                # If the file doesn't exist, create dummy data
                SITES_CACHE = [
                    {"name": "Site 1", "url_format": "https://site1.com/{username}"},
                    {"name": "Site 2", "url_format": "https://site2.com/{username}"},
                    {"name": "Site 3", "url_format": "https://site3.com/{username}"}
                ]
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                SITES_CACHE = data.get('sites', [])
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    response = jsonify({'sites': SITES_CACHE})
    response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
    return response

@app.route('/status', methods=['GET'])
def get_status():
    response = jsonify({'server_status': 'running'})
    response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
    return response

@app.route('/')
def home():
    return 'Keser API is running in simulation mode!'

if __name__ == '__main__':
    print("Starting server on port 10000...")
    app.run(host='0.0.0.0', port=10000, threaded=True)
