"""Async HTTP client for communicating with the Banking REST API.

Handles authentication (Bearer token), OpenAPI spec fetching,
and generic API calls with path/query params and JSON body.
"""

import os
from typing import Any, Dict, Optional

import httpx

# Configured via environment variables in Docker Compose
API_BASE_URL = os.environ.get("API_BASE_URL", "http://api:8000")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")


async def fetch_openapi_spec() -> Dict[str, Any]:
    """Fetch the OpenAPI specification from the REST API.

    Returns:
        Parsed OpenAPI JSON as a dict.

    Raises:
        httpx.HTTPError: If the API is unreachable or returns an error.
    """
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
    """Make an authenticated request to the REST API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.).
        path: URL path (e.g. '/clientes/').
        params: Query/path parameters dict.
        body: Optional JSON request body dict.

    Returns:
        Parsed JSON response as a dict.
        For 204 No Content, returns {"status": "deleted"}.

    Raises:
        httpx.HTTPError: If the API returns an error status.
    """
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
