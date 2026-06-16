"""Unit tests for mcp_server.generator — OpenAPI → MCP Tool conversion.

Tests cover:
  - _extract_input_schema: path params, query params, request body
  - required field is always a list (never None) per JSON Schema spec
  - _build_tool_from_operation: Tool creation from operation
  - Edge cases: no parameters, no operationId, empty spec
"""

from mcp_server.generator import _extract_input_schema, _build_tool_from_operation


class TestExtractInputSchema:
    """Scenario: building JSON Schema from OpenAPI operation definitions."""

    def test_no_parameters_returns_empty_required(self):
        """required must be an empty list when no params exist (not None)."""
        schema = _extract_input_schema({"parameters": []})
        assert schema["required"] == []

    def test_no_parameters_key_returns_empty_required(self):
        """required must be [] when parameters key is missing."""
        schema = _extract_input_schema({})
        assert schema["required"] == []

    def test_path_parameter_added_to_required(self):
        """Path parameters marked as required must appear in the required list."""
        schema = _extract_input_schema({
            "parameters": [
                {"name": "item_id", "in": "path", "required": True, "description": "ID of the item"},
            ]
        })
        assert schema["required"] == ["item_id"]
        assert schema["properties"]["item_id"]["type"] == "string"

    def test_query_parameter_optional_not_in_required(self):
        """Optional query params must NOT appear in the required list."""
        schema = _extract_input_schema({
            "parameters": [
                {"name": "skip", "in": "query", "schema": {"type": "integer", "default": 0}},
            ]
        })
        assert schema["required"] == []

    def test_query_parameter_required_in_list(self):
        """Required query params must appear in the required list."""
        schema = _extract_input_schema({
            "parameters": [
                {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}},
            ]
        })
        assert schema["required"] == ["q"]

    def test_path_and_query_params_combined(self):
        """Both path and query required params must be in required."""
        schema = _extract_input_schema({
            "parameters": [
                {"name": "id", "in": "path", "required": True},
                {"name": "limit", "in": "query", "required": True, "schema": {"type": "integer"}},
                {"name": "offset", "in": "query", "schema": {"type": "integer"}},
            ]
        })
        assert "id" in schema["required"]
        assert "limit" in schema["required"]
        assert "offset" not in schema["required"]

    def test_request_body_added_as_nested_object(self):
        """Request body with application/json must be nested under 'body' key."""
        schema = _extract_input_schema({
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "nombre": {"type": "string"},
                                "email": {"type": "string", "format": "email"},
                            },
                            "required": ["nombre"],
                        }
                    }
                }
            }
        })
        assert "body" in schema["properties"]
        assert schema["properties"]["body"]["type"] == "object"
        assert "nombre" in schema["properties"]["body"]["properties"]

    def test_mixed_path_params_and_body(self):
        """Path params and request body must coexist."""
        schema = _extract_input_schema({
            "parameters": [
                {"name": "item_id", "in": "path", "required": True},
            ],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        }
                    }
                }
            },
        })
        assert "item_id" in schema["required"]
        assert "body" in schema["properties"]
        assert schema["required"] == ["item_id"]


class TestBuildToolFromOperation:
    """Scenario: converting an OpenAPI operation into an MCP Tool."""

    def test_returns_tool_with_operation_id(self):
        """Tool name must match the operationId."""
        tool = _build_tool_from_operation("/clientes/", "get", {
            "operationId": "list_all_clientes__get",
            "summary": "List all clients",
        })
        assert tool is not None
        assert tool.name == "list_all_clientes__get"

    def test_returns_none_without_operation_id(self):
        """Operations without operationId must be skipped."""
        tool = _build_tool_from_operation("/clientes/", "get", {})
        assert tool is None

    def test_input_schema_has_required_array(self):
        """Tool inputSchema.required must always be a list."""
        tool = _build_tool_from_operation("/clientes/", "get", {
            "operationId": "list_all_clientes__get",
            "summary": "List all clients",
            "parameters": [],
        })
        assert tool is not None
        assert isinstance(tool.inputSchema.get("required"), list)
