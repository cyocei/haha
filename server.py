from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time
from functools import wraps

app = Flask(__name__)
# Configure CORS with specific settings
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

@app.route('/check', methods=['POST', 'OPTIONS'])
@rate_limit
def check_username():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response

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
            'User-Agent': USER_AGENTS[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        try:
            # Increased timeout to 30 seconds and added connection timeout
            response = requests.get(
                url, 
                headers=headers, 
                timeout=(5, 30),  # (connection timeout, read timeout)
                allow_redirects=True,
                verify=False  # Disable SSL verification for problematic sites
            )
        except requests.Timeout:
            return jsonify({
                'error': 'Request timed out',
                'exists': False,
                'status': 408,
                'final_url': url
            }), 408
        except requests.RequestException as e:
            return jsonify({
                'error': str(e),
                'exists': False,
                'status': 500,
                'final_url': url
            }), 500
        
        final_url = response.url
        
        common_error_strings = [
            "404", "not found", "error", "does not exist",
            "page not found", "no user", "not available",
            "profile not found", "user not found"
        ]
        
        exists = False
        
        if e_string and e_string.lower() in response.text.lower():
            if m_string:
                exists = m_string.lower() not in response.text.lower()
            else:
                exists = True
        elif m_string and m_string.lower() not in response.text.lower():
            exists = True
        else:
            if response.status_code == e_code:
                exists = True
                for error_string in common_error_strings:
                    if error_string.lower() in response.text.lower():
                        exists = False
                        break
            
            if exists and any(err in final_url.lower() for err in ["404", "error", "not-found"]):
                exists = False

        result = {
            'status': response.status_code,
            'exists': exists,
            'final_url': final_url
        }
        
        response = jsonify(result)
        return response

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'exists': False}), 500

@app.route('/metadata', methods=['GET', 'OPTIONS'])
@rate_limit
def get_metadata():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response

    try:
        with open('sites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            sites = [site for site in data.get('sites', []) 
                    if all(k in site for k in ['name', 'uri_check', 'cat']) and
                    (('e_string' in site and site['e_string']) or 
                     ('m_string' in site and site['m_string']))]
            response = jsonify({'sites': sites})
            return response
    except Exception as e:
        return jsonify({'error': f'Failed to load metadata: {str(e)}'}), 500

@app.route('/')
def home():
    return 'Keser API is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
else:
    application = app 
