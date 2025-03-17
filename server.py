from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import asyncio
import json
import random
import logging
import time
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
]

# Create a connection pool that can be reused across requests
connector = TCPConnector(limit=50, ttl_dns_cache=60, ssl=False)
timeout = ClientTimeout(total=10)

class CheckRequest(BaseModel):
    urls: List[str]
    e_string: Optional[str] = None
    m_string: Optional[str] = None
    e_code: Optional[int] = None
    m_code: Optional[int] = None

# This ClientSession is created on startup and closed on shutdown
session: ClientSession = None

@app.on_event("startup")
async def startup_event():
    global session
    session = ClientSession(connector=connector, timeout=timeout)

@app.on_event("shutdown")
async def shutdown_event():
    if session:
        await session.close()

async def check_single_site(url, e_string, m_string, e_code, m_code):
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }

        async with session.get(url, headers=headers, allow_redirects=True) as response:
            try:
                text = await response.text()
                status = response.status

                # Fast path: check existence first
                if status == e_code and e_string in text:
                    return {
                        'status': status,
                        'exists': True,
                        'final_url': str(response.url),
                        'text': None  # Don't return the text to save bandwidth
                    }

                # Check for explicit non-existence
                if m_code is not None and m_string is not None:
                    if status == m_code and m_string in text:
                        return {
                            'status': status,
                            'exists': False,
                            'final_url': str(response.url),
                            'text': None
                        }

                # Default case
                return {
                    'status': status,
                    'exists': False,
                    'final_url': str(response.url),
                    'text': None
                }

            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                text = await response.read()
                text = text.decode('latin-1')
                return {
                    'status': response.status,
                    'exists': False,
                    'final_url': str(response.url),
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

@app.post("/check")
async def check_username(request: CheckRequest):
    try:
        urls = request.urls
        e_string = request.e_string
        m_string = request.m_string
        e_code = request.e_code
        m_code = request.m_code

        # Process sites concurrently
        tasks = [check_single_site(url, e_string, m_string, e_code, m_code) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={'error': str(e), 'exists': False}
        )

# Cache for metadata
metadata_cache = None
metadata_cache_time = 0
CACHE_DURATION = 300  # 5 minutes

@app.get("/metadata")
async def get_metadata():
    global metadata_cache, metadata_cache_time
    current_time = time.time()

    try:
        # Return cached data if available and fresh
        if metadata_cache and (current_time - metadata_cache_time) < CACHE_DURATION:
            return metadata_cache

        # Read fresh data
        with open('sites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            metadata_cache = {'sites': data.get('sites', [])}
            metadata_cache_time = current_time
            return metadata_cache
    except Exception as e:
        logger.error(f"Error fetching metadata: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )

@app.get("/")
async def home():
    return "Keser API is running!"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
