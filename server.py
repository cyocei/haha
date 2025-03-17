from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import random
import logging
import time
import concurrent.futures

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
]

# No more asyncio or aiohttp - using synchronous requests with thread pool
def check_single_site(url, e_string, m_string, e_code, m_code):
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }

        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        status = response.status_code
        
        try:
            text = response.text
            
            # Fast path: check existence first
            if status == e_code and e_string in text:
                return {
                    'status': status,
                    'exists': True,
                    'final_url': response.url,
                    'text': text if app.debug else None
                }

            # Check for explicit non-existence
            if m_code is not None and m_string is not None:
                if status == m_code and m_string in text:
                    return {
                        'status': status,
                        'exists': False,
                        'final_url': response.url,
                        'text': text if app.debug else None
                    }

            # Default case
            return {
                'status': status,
                'exists': False,
                'final_url': response.url,
                'text': text if app.debug else None
            }

        except UnicodeDecodeError:
            # Should be handled by requests automatically
            return {
                'status': status,
                'exists': False,
                'final_url': response.url,
                'text': None
            }

    except Exception as e:
        logger.error(f"Error checking {url}: {str(e)}")
        return {
            'exists': False,
            'status': 0,
            'error': str(e),
            'final_url': url
        }

def check_multiple_sites(urls, e_string, m_string, e_code, m_code):
    # Use thread pool for concurrent requests without asyncio
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_single_site, url, e_string, m_string, e_code, m_code) for url in urls]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
        return results

@app.route('/check', methods=['POST', 'OPTIONS'])
def check_username():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        data = request.get_json()
        if not data or 'urls' not in data:
            return jsonify({'error': 'Missing URLs parameter'}), 400

        urls = data['urls']
        e_string = data.get('e_string')
        m_string = data.get('m_string')
        e_code = data.get('e_code')
        m_code = data.get('m_code')

        # Fully synchronous operation using thread pool
        results = check_multiple_sites(urls, e_string, m_string, e_code, m_code)
        return jsonify(results)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e), 'exists': False}), 500

# Cache for metadata
metadata_cache = None
metadata_cache_time = 0
CACHE_DURATION = 300  # 5 minutes

@app.route('/metadata', methods=['GET', 'OPTIONS'])
def get_metadata():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    global metadata_cache, metadata_cache_time
    current_time = time.time()

    try:
        # Return cached data if available and fresh
        if metadata_cache and (current_time - metadata_cache_time) < CACHE_DURATION:
            return jsonify(metadata_cache)

        # Read fresh data
        with open('sites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            metadata_cache = {'sites': data.get('sites', [])}
            metadata_cache_time = current_time
            return jsonify(metadata_cache)
    except Exception as e:
        logger.error(f"Error fetching metadata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return 'Keser API is running!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
