import os
from typing import Any, Dict, Optional

import httpx

API_BASE_URL = os.environ.get("API_BASE_URL", "http://api:8000")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")


async def fetch_openapi_spec() -> Dict[str, Any]:
    url = f"{API_BASE_URL}/openapi.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()


async def call_api(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    url = f"{API_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=method,
            url=url,
            params=params,
            json=body,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        if resp.status_code == 204:
            return {"status": "deleted"}
        return resp.json()
