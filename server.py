from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import logging

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
            session = requests.Session()
            response = session.get(
                url, 
                headers=headers, 
                timeout=(5, 15),  # Increased timeouts
                allow_redirects=True,
                verify=False
            )
            
            final_url = response.url
            response_text = response.text.lower()
            
            # Initialize as False
            exists = False
            
            # Check status code first
            if response.status_code == e_code:
                exists = True
            elif response.status_code == m_code:
                exists = False
            
            # If e_string is provided, it takes precedence
            if e_string:
                e_string_lower = e_string.lower()
                if e_string_lower in response_text:
                    exists = True
                    # Only check m_string if e_string was found
                    if m_string and m_string.lower() in response_text:
                        exists = False
            # If only m_string is provided
            elif m_string and m_string.lower() not in response_text:
                exists = True
            
            # Additional validation only if exists is True
            if exists:
                # Check for common error indicators in URL
                error_indicators = ["404", "error", "not-found", "notfound"]
                if any(indicator in final_url.lower() for indicator in error_indicators):
                    exists = False
                
                # Check for error messages in content
                error_messages = [
                    "404", "not found", "error", "does not exist",
                    "page not found", "no user", "not available",
                    "profile not found", "user not found",
                    "account not found", "user does not exist"
                ]
                if any(msg in response_text for msg in error_messages):
                    exists = False

            return jsonify({
                'status': response.status_code,
                'exists': exists,
                'final_url': final_url,
                'text': response.text
            })

        except requests.Timeout:
            return jsonify({
                'exists': False,
                'status': 408,
                'final_url': url
            })
        except requests.RequestException:
            return jsonify({
                'exists': False,
                'status': 500,
                'final_url': url
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
