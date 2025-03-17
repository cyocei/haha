from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import os
import aiohttp
import asyncio
from datetime import datetime
from aiohttp.resolver import AsyncResolver
import random
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.debug = False  # Ensure debug is off in production for better performance

# Enable CORS for all routes and allow specific origins
CORS(app, resources={
    r"/*": {
        "origins": ["https://vbiskit.com"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for running asyncio tasks
thread_pool = ThreadPoolExecutor(max_workers=4)

# User agents list (keep the same as your original code)
USER_AGENTS = [
   "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.94 Chrome/37.0.2062.94 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9",
    "Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/7.1.8 Safari/537.85.17",
    "Mozilla/5.0 (iPad; CPU OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4",
    "Mozilla/5.0 (iPad; CPU OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F69 Safari/600.1.4",
    "Mozilla/5.0 (Windows NT 6.1; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.6.3 (KHTML, like Gecko) Version/8.0.6 Safari/600.6.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.5.17 (KHTML, like Gecko) Version/8.0.5 Safari/600.5.17",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (iPad; CPU OS 7_1_2 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D257 Safari/9537.53",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS x86_64 7077.134.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.156 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/7.1.7 Safari/537.85.16",
    "Mozilla/5.0 (Windows NT 6.0; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (iPad; CPU OS 8_1_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B466 Safari/600.1.4",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko) Version/8.0.3 Safari/600.3.18",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 8_1_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B440 Safari/600.1.4",
    "Mozilla/5.0 (Linux; U; Android 4.0.3; en-us; KFTT Build/IML74K) AppleWebKit/537.36 (KHTML, like Gecko) Silk/3.68 like Chrome/39.0.2171.93 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 8_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12D508 Safari/600.1.4",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0",
    "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
    "Mozilla/5.0 (Linux; U; Android 4.4.3; en-us; KFTHWI Build/KTU84M) AppleWebKit/537.36 (KHTML, like Gecko) Silk/3.68 like Chrome/39.0.2171.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.6.3 (KHTML, like Gecko) Version/7.1.6 Safari/537.85.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.4.10 (KHTML, like Gecko) Version/8.0.4 Safari/600.4.10",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.78.2 (KHTML, like Gecko) Version/7.0.6 Safari/537.78.2",
    "Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) CriOS/45.0.2454.68 Mobile/12H321 Safari/600.1.4",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; Trident/7.0; Touch; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B410 Safari/600.1.4",
    "Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.53",
    "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; TNJB; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; ARM; Trident/7.0; Touch; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; MDDCJS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4",
    "Mozilla/5.0 (Linux; U; Android 4.4.3; en-us; KFASWI Build/KTU84M) AppleWebKit/537.36 (KHTML, like Gecko) Silk/3.68 like Chrome/39.0.2171.93 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) GSA/7.0.55539 Mobile/12H321 Safari/600.1.4",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; MATBJS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Linux; U; Android 4.0.4; en-us; KFJWI Build/IMM76D) AppleWebKit/537.36 (KHTML, like Gecko) Silk/3.68 like Chrome/39.0.2171.93 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 7_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D167 Safari/9537.53",
    "Mozilla/5.0 (X11; CrOS armv7l 7077.134.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.156 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/7.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/600.2.5 (KHTML, like Gecko) Version/8.0.2 Safari/600.2.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11) AppleWebKit/601.1.56 (KHTML, like Gecko) Version/9.0 Safari/601.1.56",
    "Mozilla/5.0 (Linux; U; Android 4.4.3; en-us; KFSOWI Build/KTU84M) AppleWebKit/537.36 (KHTML, like Gecko) Silk/3.68 like Chrome/39.0.2171.93 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 5_1_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B206 Safari/7534.48.3",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko)"
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Create a semaphore to limit concurrent connections per domain
# This helps prevent rate limiting and improve reliability
SEMAPHORES = {}
MAX_CONNECTIONS_PER_DOMAIN = 5

def get_domain_semaphore(domain):
    if domain not in SEMAPHORES:
        SEMAPHORES[domain] = asyncio.Semaphore(MAX_CONNECTIONS_PER_DOMAIN)
    return SEMAPHORES[domain]

async def fetch(session, url, e_string, m_string, e_code, m_code):
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }

    # Extract domain for semaphore
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    semaphore = get_domain_semaphore(domain)

    try:
        # Use semaphore to limit connections per domain
        async with semaphore:
            start_time = datetime.now()
            
            # Reduce timeout for faster checks
            async with session.get(url, headers=headers, timeout=5.0, ssl=False) as response:
                # Only read text if needed for pattern matching
                if e_string or m_string:
                    text = await response.text()
                else:
                    text = ""

                if response.status == e_code and (not e_string or e_string in text):
                    result = {
                        'status': response.status,
                        'exists': True,
                        'final_url': str(response.url),
                        'text': text if app.debug else None
                    }
                elif m_code is not None and m_string is not None and response.status == m_code and m_string in text:
                    result = {
                        'status': response.status,
                        'exists': False,
                        'final_url': str(response.url),
                        'text': text if app.debug else None
                    }
                else:
                    result = {
                        'status': response.status,
                        'exists': False,
                        'final_url': str(response.url),
                        'text': text if app.debug else None
                    }

                end_time = datetime.now()
                logger.info(f"Processed {url} in {(end_time - start_time).total_seconds():.2f} seconds")
                return result

    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {url}")
        return {
            'exists': False,
            'status': 0,
            'error': 'Timeout',
            'final_url': url
        }
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return {
            'exists': False,
            'status': 0,
            'error': str(e),
            'final_url': url
        }

async def process_requests(urls, e_string, m_string, e_code, m_code):
    # Use Cloudflare DNS for potentially faster lookups
    resolver = AsyncResolver(nameservers=["1.1.1.1", "1.0.0.1"])
    
    # Configure connector with optimized settings
    connector = aiohttp.TCPConnector(
        limit=200,  # Increase connection limit
        resolver=resolver,
        ttl_dns_cache=300,  # Cache DNS results longer
        use_dns_cache=True,
        force_close=False,  # Keep connections alive when possible
    )
    
    # Configure client session with optimized timeouts
    timeout = aiohttp.ClientTimeout(total=10.0, connect=2.0)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [fetch(session, url, e_string, m_string, e_code, m_code) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

def run_async_check(urls, e_string, m_string, e_code, m_code):
    """Run the async function in the current thread"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(process_requests(urls, e_string, m_string, e_code, m_code))
    finally:
        loop.close()

@app.route('/check', methods=['POST', 'OPTIONS'])
def check_username():
    if request.method == 'OPTIONS':
        # Preflight request handling
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
        e_string = data.get('e_string')
        m_string = data.get('m_string')
        e_code = data.get('e_code')
        m_code = data.get('m_code')

        # Use thread pool to avoid blocking Flask
        results = thread_pool.submit(
            run_async_check, [url], e_string, m_string, e_code, m_code
        ).result()
        
        result = results[0]  # Get the first (and only) result

        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        return response

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e), 'exists': False}), 500

@app.route('/batch_check', methods=['POST', 'OPTIONS'])
def batch_check_usernames():
    if request.method == 'OPTIONS':
        # Preflight request handling
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
        default_e_string = data.get('e_string')
        default_m_string = data.get('m_string')
        default_e_code = data.get('e_code')
        default_m_code = data.get('m_code')

        # Calculate start time for metrics
        start_time = datetime.now()
        
        # Process in batches of 100 URLs maximum
        BATCH_SIZE = 100
        all_results = {}
        
        for i in range(0, len(urls), BATCH_SIZE):
            batch_urls = urls[i:i+BATCH_SIZE]
            batch_results = thread_pool.submit(
                run_async_check, 
                batch_urls, default_e_string, default_m_string, default_e_code, default_m_code
            ).result()
            
            # Add results to combined dictionary
            all_results.update(dict(zip(batch_urls, batch_results)))
            
            # Log batch completion
            completed = min(i + BATCH_SIZE, len(urls))
            logger.info(f"Completed {completed}/{len(urls)} URLs")
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        logger.info(f"Processed {len(urls)} URLs in {total_time:.2f} seconds ({len(urls) / total_time:.2f} URLs/sec)")

        response = jsonify({'results': all_results})
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        return response

    except Exception as e:
        logger.error(f"Error processing batch request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/metadata', methods=['GET', 'OPTIONS'])
def get_metadata():
    if request.method == 'OPTIONS':
        # Preflight request handling
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response

    try:
        # Cache mechanism for metadata
        if not hasattr(app, 'metadata_cache'):
            # Ensure the file path is correct
            file_path = 'sites.json'
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return jsonify({'error': 'File not found'}), 404

            # Open and read the file once
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'sites' not in data:
                logger.error(f"Invalid JSON structure: 'sites' key missing")
                return jsonify({'error': 'Invalid JSON structure'}), 500
                
            # Cache the data
            app.metadata_cache = data['sites']
            
        response = jsonify({'sites': app.metadata_cache})
        response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
        return response

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({'error': 'Invalid JSON format'}), 500

    except Exception as e:
        logger.error(f"Error reading metadata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Endpoint to get the status of the server"""
    response = jsonify({
        'server_status': 'running'
    })
    response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
    return response

@app.route('/')
def home():
    return 'Keser API is running!'

if __name__ == '__main__':
    # Use a production-ready WSGI server like gunicorn in production
    app.run(host='0.0.0.0', port=10000, threaded=True)
