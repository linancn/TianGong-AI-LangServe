import aiohttp
from typing import Optional

from src.config.config import (
    END_POINT,
    BEARER_TOKEN,
    EMAIL,
    PASSWORD,
    X_REGION,
)


async def search(
    query: str,
    top_k: Optional[int] = 8,
    ext_k: Optional[int] = 0,
    max_top_k: int = 16,
    max_ext_k: int = 3,
) -> list:

    url = END_POINT + "textbook_search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "email": EMAIL,
        "password": PASSWORD,
        "x-region": X_REGION
    }

    request_body = {
        "query": query,
        "topK": min(top_k, max_top_k),
        "extK": min(ext_k, max_ext_k),
    }

    # try:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=request_body) as response:
            response.raise_for_status()
            docs_list = await response.json()
            return docs_list
