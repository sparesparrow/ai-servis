"""Unit tests for MCP Framework"""

import pytest
import asyncio
from modules.mcp_framework import MCPServer, MCPMessage, Tool, create_tool


@pytest.mark.asyncio
async def test_mcp_message_creation():
    """Test MCP message creation and serialization"""
    message = MCPMessage(
        id="test-1",
        method="test/method",
        params={"key": "value"}
    )
    
    assert message.id == "test-1"
    assert message.method == "test/method"
    assert message.params == {"key": "value"}
    
    # Test JSON serialization
    json_str = message.to_json()
    assert "test-1" in json_str
    assert "test/method" in json_str


def test_tool_creation():
    """Test tool creation"""
    def dummy_handler(param1: str) -> str:
        return f"Result: {param1}"
    
    tool = create_tool(
        name="test_tool",
        description="A test tool",
        schema={
            "type": "object",
            "properties": {
                "param1": {"type": "string"}
            }
        },
        handler=dummy_handler
    )
    
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert tool.handler == dummy_handler


@pytest.mark.asyncio
async def test_mcp_server_initialization():
    """Test MCP server initialization"""
    server = MCPServer("test-server", "1.0.0")
    
    assert server.name == "test-server"
    assert server.version == "1.0.0"
    assert len(server.tools) == 0
    assert not server.initialized
