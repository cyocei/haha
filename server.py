from flask import Flask, request, jsonify
from flask_cors import CORS
import aiohttp
import asyncio
import json
import logging
from aiohttp import ClientTimeout
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Extremely aggressive timeout
TIMEOUT = ClientTimeout(total=5, connect=1, sock_read=3)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

def get_random_user_agent():
    import random
    return random.choice(USER_AGENTS)

async def check_single_site(session, url, e_string, m_string, e_code):
    try:
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        async with session.get(url, headers=headers, timeout=TIMEOUT, ssl=False) as response:
            final_url = str(response.url)
            text = await response.text()
            text_lower = text.lower()
            final_url_lower = final_url.lower()

            exists = False
            if any(err in final_url_lower for err in ["404", "error", "not-found"]):
                exists = False
            elif e_string and e_string.lower() in text_lower:
                exists = not (m_string and m_string.lower() in text_lower)
            elif m_string and m_string.lower() not in text_lower:
                exists = True
            elif response.status == e_code:
                exists = not any(err in text_lower for err in [
                    "404", "not found", "error", "does not exist",
                    "page not found", "no user", "not available"
                ])

            return {
                'status': response.status,
                'exists': exists,
                'final_url': final_url
            }

    except asyncio.TimeoutError:
        return {'exists': False, 'status': 408, 'final_url': url}
    except Exception:
        return {'exists': False, 'status': 500, 'final_url': url}

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

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0)) as session:
            result = await check_single_site(session, url, e_string, m_string, e_code)
            return jsonify(result)

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
