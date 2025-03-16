from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import logging
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "max_age": 3600,
        "supports_credentials": True
    }
})

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create thread pool for concurrent requests
executor = ThreadPoolExecutor(max_workers=60)

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
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL parameter'}), 400

        url = data['url']
        e_string = data.get('e_string')
        m_string = data.get('m_string')
        e_code = data.get('e_code', 200)
        m_code = data.get('m_code', 404)

        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        try:
            # Reduced timeouts for faster checking
            response = requests.get(
                url, 
                headers=headers, 
                timeout=(3, 10),  # Reduced timeouts (connection, read)
                allow_redirects=True,
                verify=False
            )
        except requests.Timeout:
            return jsonify({
                'exists': False,
                'status': 408,
                'final_url': url
            }), 408
        except requests.RequestException:
            return jsonify({
                'exists': False,
                'status': 500,
                'final_url': url
            }), 500
        
        final_url = response.url
        
        # Optimized error checking
        exists = False
        response_text_lower = response.text.lower()
        final_url_lower = final_url.lower()
        
        # Quick checks first
        if any(err in final_url_lower for err in ["404", "error", "not-found"]):
            exists = False
        elif e_string and e_string.lower() in response_text_lower:
            exists = not (m_string and m_string.lower() in response_text_lower)
        elif m_string and m_string.lower() not in response_text_lower:
            exists = True
        elif response.status_code == e_code:
            exists = not any(err in response_text_lower for err in [
                "404", "not found", "error", "does not exist",
                "page not found", "no user", "not available",
                "profile not found", "user not found"
            ])

        return jsonify({
            'status': response.status_code,
            'exists': exists,
            'final_url': final_url
        })

    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'exists': False}), 500

@app.route('/metadata', methods=['GET', 'OPTIONS'])
def get_metadata():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        with open('sites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Pre-filter valid sites
            sites = [site for site in data.get('sites', []) 
                    if all(k in site for k in ['name', 'uri_check', 'cat']) and
                    (('e_string' in site and site['e_string']) or 
                     ('m_string' in site and site['m_string']))]
            return jsonify({'sites': sites})
    except Exception as e:
        logger.error(f"Failed to load metadata: {str(e)}")
        return jsonify({'error': f'Failed to load metadata: {str(e)}'}), 500

@app.route('/')
def home():
    return 'Keser API is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
else:
    application = app
