from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

def get_random_user_agent():
    import random
    return random.choice(USER_AGENTS)

@app.route('/check', methods=['POST', 'OPTIONS'])
def check_username():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL parameter'}), 400

        url = data['url']
        e_string = data.get('e_string')
        m_string = data.get('m_string')

        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }

        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=30,
                allow_redirects=True,
                verify=False
            )
            
            exists = True  # Default to True
            
            # Only mark as False if we're absolutely sure it doesn't exist
            if response.status_code == 404:
                exists = False
            elif "404" in response.url or "not-found" in response.url:
                exists = False
            elif m_string and m_string.lower() in response.text.lower():
                exists = False
            
            return jsonify({
                'status': response.status_code,
                'exists': exists,
                'final_url': response.url,
                'text': response.text
            })

        except:
            # If any error occurs, assume the profile might exist
            return jsonify({
                'exists': True,
                'status': 200,
                'final_url': url
            })

    except Exception as e:
        return jsonify({'error': str(e), 'exists': True}), 200

@app.route('/metadata', methods=['GET', 'OPTIONS'])
def get_metadata():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        with open('sites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Return ALL sites
            return jsonify({'sites': data.get('sites', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return 'Keser API is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
else:
    application = app
