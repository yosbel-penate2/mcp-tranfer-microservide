"""Dynamic MCP Tool generator from OpenAPI specification.

Fetches the REST API's OpenAPI spec at runtime and
creates corresponding MCP Tools for each operation.
A generic handler dispatches tool calls to the REST API.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import Tool

from mcp_server.api_client import call_api, fetch_openapi_spec

logger = logging.getLogger(__name__)


def _extract_input_schema(
    path_def: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a JSON Schema input schema from an OpenAPI path definition.

    Handles path parameters, query parameters, and request body
    (application/json). Body parameters are nested under a 'body' key.

    Args:
        path_def: The OpenAPI operation definition dict.

    Returns:
        JSON Schema dict suitable for MCP Tool inputSchema.
    """
    parameters = path_def.get("parameters", [])
    request_body = path_def.get("requestBody", {})

    properties: Dict[str, Any] = {}
    required: List[str] = []

    for param in parameters:
        if param.get("in") == "path":
            name = param["name"]
            properties[name] = {
                "type": "string",
                "description": param.get("description", ""),
            }
            if param.get("required"):
                required.append(name)
        elif param.get("in") == "query":
            name = param["name"]
            schema = param.get("schema", {"type": "string"})
            properties[name] = {**schema, "description": param.get("description", "")}
            if param.get("required"):
                required.append(name)

    if request_body:
        content = request_body.get("content", {})
        if "application/json" in content:
            json_schema = content["application/json"].get("schema", {})
            body_props = json_schema.get("properties", {})
            properties["body"] = {
                "type": "object",
                "properties": body_props,
                "description": "Request body",
            }
            if json_schema.get("required"):
                properties["body"]["required"] = json_schema["required"]

    return {
        "type": "object",
        "properties": properties,
        "required": required if required else [],
    }


def _build_tool_from_operation(
    path: str,
    method: str,
    operation: Dict[str, Any],
) -> Optional[Tool]:
    """Convert an OpenAPI operation into an MCP Tool definition.

    Args:
        path: URL path pattern (e.g. '/clientes/{id}').
        method: HTTP method (get, post, etc.).
        operation: OpenAPI operation dict.

    Returns:
        MCP Tool instance, or None if no operationId.
    """
    operation_id = operation.get("operationId", "")
    if not operation_id:
        return None

    summary = operation.get("summary", operation_id)
    input_schema = _extract_input_schema(operation)

    return Tool(
        name=operation_id,
        description=summary,
        inputSchema=input_schema,
    )


async def generate_tools() -> List[Tool]:
    """Fetch the OpenAPI spec and generate all MCP Tools.

    Returns:
        List of MCP Tool definitions. Empty list if spec unavailable.
    """
    try:
        spec = await fetch_openapi_spec()
    except Exception as e:
        logger.warning(f"Could not fetch OpenAPI spec: {e}")
        return []

    tools: List[Tool] = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        for method in ["get", "post", "put", "delete", "patch"]:
            operation = path_item.get(method)
            if operation is None:
                continue
            tool = _build_tool_from_operation(path, method, operation)
            if tool is not None:
                tools.append(tool)

    return tools


async def handle_tool_call(
    name: str,
    arguments: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Execute an MCP tool call by dispatching to the REST API.

    Looks up the operation by name in the OpenAPI spec,
    separates path/query params from the request body,
    and calls the REST API via the api_client.

    Args:
        name: MCP Tool name (matching operationId).
        arguments: Tool arguments dict.

    Returns:
        List with a single TextContent dict containing the API response.
    """
    try:
        spec = await fetch_openapi_spec()
    except Exception as e:
        return [{"type": "text", "text": f"Error fetching API spec: {e}"}]

    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        for method in ["get", "post", "put", "delete", "patch"]:
            operation = path_item.get(method)
            if operation is None:
                continue
            if operation.get("operationId") == name:
                params = {}
                body = None

                for key, value in arguments.items():
                    if key == "body" and isinstance(value, dict):
                        body = value
                    else:
                        params[key] = value

                try:
                    result = await call_api(
                        method.upper(), path, params=params, body=body
                    )
                    return [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, default=str),
                        }
                    ]
                except Exception as e:
                    return [{"type": "text", "text": f"Error calling API: {e}"}]

    return [{"type": "text", "text": f"Tool '{name}' not found in API spec"}]
