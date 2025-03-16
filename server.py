from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import logging
import random
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

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

# Increased thread pool for concurrent requests
executor = ThreadPoolExecutor(max_workers=50)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

async def check_url(session, url, headers, e_string, m_string, e_code, m_code):
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5), ssl=False) as response:
            text = await response.text()
            final_url = str(response.url)
            
            common_error_strings = [
                "404", "not found", "error", "does not exist",
                "page not found", "no user", "not available",
                "profile not found", "user not found"
            ]
            
            exists = False
            
            if e_string and e_string.lower() in text.lower():
                if m_string:
                    exists = m_string.lower() not in text.lower()
                else:
                    exists = True
            elif m_string and m_string.lower() not in text.lower():
                exists = True
            else:
                if response.status == e_code:
                    exists = True
                    if any(error in text.lower() for error in common_error_strings):
                        exists = False
                
                if exists and any(err in final_url.lower() for err in ["404", "error", "not-found"]):
                    exists = False

            return {
                'status': response.status,
                'exists': exists,
                'final_url': final_url,
                'text': text
            }

    except asyncio.TimeoutError:
        return {
            'error': 'Request timed out',
            'exists': False,
            'status': 408,
            'final_url': url
        }
    except Exception as e:
        logger.error(f"Error checking {url}: {str(e)}")
        return {
            'error': str(e),
            'exists': False,
            'status': 500,
            'final_url': url
        }

@app.route('/check', methods=['POST', 'OPTIONS'])
async def check_username():
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

        async with aiohttp.ClientSession() as session:
            result = await check_url(session, url, headers, e_string, m_string, e_code, m_code)
            return jsonify(result)

    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'exists': False}), 500

@app.route('/metadata', methods=['GET', 'OPTIONS'])
async def get_metadata():
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
