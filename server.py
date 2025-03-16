from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time
from functools import wraps

app = Flask(__name__)
CORS(app)

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        time.sleep(0.1)  # Simple rate limiting
        return f(*args, **kwargs)
    return decorated_function

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

@app.route('/check', methods=['POST'])
@rate_limit
def check_username():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL parameter'}), 400

        url = data['url']
        headers = {
            'User-Agent': USER_AGENTS[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(url, headers=headers, timeout=5)
        return jsonify({
            'status': response.status_code,
            'text': response.text
        })
    except requests.Timeout:
        return jsonify({'error': 'Request timed out'}), 408
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/metadata')
@rate_limit
def get_metadata():
    try:
        with open('sites.json', 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': 'Failed to load metadata'}), 500

@app.route('/')
def home():
    return 'Keser API is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
else:
    # This is used by gunicorn in production
    application = app 