from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import os
import aiohttp
import asyncio
from datetime import datetime
import random
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import signal
import time

app = Flask(__name__)
app.debug = False

# Enable CORS
CORS(app, resources={r"/*": {"origins": ["https://vbiskit.com"], "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Number of workers for multiprocessing
NUM_WORKERS = multiprocessing.cpu_count() * 2

# Your existing USER_AGENTS list
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

# Create a global session object pool
SESSION_POOL = None
MAX_CONNECTIONS = 500  # Much higher connection limit

async def setup_session_pool():
    global SESSION_POOL
    if SESSION_POOL is None:
        # Use Cloudflare DNS for faster lookups
        resolver = aiohttp.resolver.AsyncResolver(nameservers=["1.1.1.1", "1.0.0.1"])
        
        # Configure for maximum throughput
        connector = aiohttp.TCPConnector(
            limit=MAX_CONNECTIONS,
            resolver=resolver,
            ttl_dns_cache=300,
            use_dns_cache=True,
            force_close=True,  # Force close to avoid hanging connections
            enable_cleanup_closed=True
        )
        
        # Ultra-aggressive timeouts
        timeout = aiohttp.ClientTimeout(total=3.0, connect=1.0, sock_connect=1.0, sock_read=1.0)
        
        SESSION_POOL = aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            trust_env=True
        )
    
    return SESSION_POOL

async def close_session_pool():
    global SESSION_POOL
    if SESSION_POOL is not None:
        await SESSION_POOL.close()
        SESSION_POOL = None

async def fetch_with_retry(url, e_string, m_string, e_code, m_code, max_retries=1):
    """Fetch a URL with retry logic for resilience"""
    session = await setup_session_pool()
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'close'  # Don't keep connections open
    }
    
    for attempt in range(max_retries + 1):
        try:
            # Ultra-short timeout for faster overall performance
            async with session.get(url, headers=headers, ssl=False, allow_redirects=True, timeout=1.5) as response:
                # Only fetch text if absolutely needed
                if (e_string and response.status == e_code) or (m_string and response.status == m_code):
                    # Read with timeout protection
                    try:
                        text = await asyncio.wait_for(response.text(), timeout=1.0)
                    except asyncio.TimeoutError:
                        text = ""
                else:
                    text = ""
                
                # Process response
                if response.status == e_code and (not e_string or e_string in text):
                    return {
                        'status': response.status,
                        'exists': True,
                        'final_url': str(response.url)
                    }
                elif m_code is not None and response.status == m_code and (not m_string or m_string in text):
                    return {
                        'status': response.status,
                        'exists': False,
                        'final_url': str(response.url)
                    }
                else:
                    return {
                        'status': response.status,
                        'exists': False,
                        'final_url': str(response.url)
                    }
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < max_retries:
                # Small delay before retry
                await asyncio.sleep(0.1)
                continue
            else:
                return {
                    'exists': False,
                    'status': 0,
                    'error': str(e),
                    'final_url': url
                }
        
        except Exception as e:
            return {
                'exists': False,
                'status': 0,
                'error': str(e),
                'final_url': url
            }

async def process_urls_chunk(urls, e_string, m_string, e_code, m_code):
    """Process a chunk of URLs in parallel with aggressive timeouts"""
    tasks = []
    for url in urls:
        # Add a small delay between task creation to avoid overwhelming connections
        task = asyncio.create_task(fetch_with_retry(url, e_string, m_string, e_code, m_code))
        tasks.append((url, task))
    
    results = {}
    for url, task in tasks:
        try:
            # Apply timeout to the entire task
            result = await asyncio.wait_for(task, timeout=2.0)
            results[url] = result
        except asyncio.TimeoutError:
            results[url] = {
                'exists': False,
                'status': 0,
                'error': 'Task timeout',
                'final_url': url
            }
    
    return results

async def process_all_urls(urls, e_string, m_string, e_code, m_code):
    """Process all URLs with chunking for better performance"""
    # Optimal chunk size determined by testing
    CHUNK_SIZE = 10
    all_results = {}
    
    # Process in smaller chunks for better parallelism
    for i in range(0, len(urls), CHUNK_SIZE):
        chunk = urls[i:i+CHUNK_SIZE]
        chunk_results = await process_urls_chunk(chunk, e_string, m_string, e_code, m_code)
        all_results.update(chunk_results)
    
    return all_results

# Wrapper function to run in a process
def process_in_subprocess(urls, e_string, m_string, e_code, m_code):
    """Execute the async code in a separate process"""
    # Set shorter default socket timeout
    import socket
    socket.setdefaulttimeout(2.0)
    
    # Create and run a new event loop
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    
    try:
        # Run with timeout protection for the entire operation
        return loop.run_until_complete(
            asyncio.wait_for(
                process_all_urls(urls, e_string, m_string, e_code, m_code),
                timeout=5.0
            )
        )
    except asyncio.TimeoutError:
        # Return partial results on timeout
        logger.error("Subprocess timed out")
        return {url: {'exists': False, 'status': 0, 'error': 'Global timeout'} for url in urls}
    finally:
        try:
            # Cleanup session
            loop.run_until_complete(close_session_pool())
            loop.close()
        except:
            pass

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
        e_string = data.get('e_string')
        m_string = data.get('m_string')
        e_code = data.get('e_code')
        m_code = data.get('m_code')

        # Run single check directly
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(process_in_subprocess, [url], e_string, m_string, e_code, m_code)
            results = future.result()
        
        result = results.get(url, {'exists': False, 'status': 0, 'error': 'Processing error'})

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
        e_string = data.get('e_string')
        m_string = data.get('m_string')
        e_code = data.get('e_code')
        m_code = data.get('m_code')

        # Calculate start time for metrics
        start_time = datetime.now()
        
        # For small batches, process in a single subprocess
        if len(urls) <= 33:
            with ProcessPoolExecutor(max_workers=1) as executor:
                future = executor.submit(process_in_subprocess, urls, e_string, m_string, e_code, m_code)
                results = future.result()
        else:
            # For larger batches, split across multiple processes
            results = {}
            chunk_size = max(5, len(urls) // NUM_WORKERS)
            futures = []
            
            with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
                # Submit tasks
                for i in range(0, len(urls), chunk_size):
                    chunk = urls[i:i+chunk_size]
                    future = executor.submit(process_in_subprocess, chunk, e_string, m_string, e_code, m_code)
                    futures.append(future)
                
                # Collect results
                for future in futures:
                    chunk_result = future.result()
                    results.update(chunk_result)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        logger.info(f"Processed {len(urls)} URLs in {total_time:.2f} seconds ({len(urls) / total_time:.2f} URLs/sec)")

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

    # In-memory cache
    if not hasattr(app, 'metadata_cache') or app.metadata_cache is None:
        try:
            file_path = 'sites.json'
            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 404

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'sites' not in data:
                return jsonify({'error': 'Invalid JSON structure'}), 500
                
            app.metadata_cache = data['sites']
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    response = jsonify({'sites': app.metadata_cache})
    response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
    return response

@app.route('/status', methods=['GET'])
def get_status():
    response = jsonify({'server_status': 'running'})
    response.headers.add('Access-Control-Allow-Origin', 'https://vbiskit.com')
    return response

@app.route('/')
def home():
    return 'Keser API is running in turbo mode!'

def signal_handler(sig, frame):
    """Clean shutdown on SIGINT/SIGTERM"""
    logger.info("Shutdown signal received, exiting...")
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers
    import sys
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the app with production server
    from waitress import serve
    print("Starting server with Waitress on port 10000...")
    serve(app, host='0.0.0.0', port=10000, threads=16)
