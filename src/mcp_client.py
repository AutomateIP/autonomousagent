"""MCP client implementation using FastMCP."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastmcp import Client

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for a single MCP server using FastMCP."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize MCP client for a specific server.
        
        Args:
            name: Server name
            config: Server configuration dict with command, args, type, etc.
        """
        self.name = name
        self.config = config
        self.client: Optional[Client] = None
        self._tools: List[Dict[str, Any]] = []
    
    async def connect(self) -> bool:
        """
        Connect to the MCP server using FastMCP Client.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MCP server: {self.name}")
            
            if self.config.get("disabled", False):
                logger.info(f"Server {self.name} is disabled, skipping")
                return False
            
            # Check transport type
            transport_type = self.config.get("type", "stdio")
            if transport_type == "http":
                logger.warning(f"HTTP transport not yet implemented for {self.name}, skipping")
                logger.info(f"To use {self.name}, HTTP transport support needs to be added to MCPClient")
                return False
            
            # Convert our config format to FastMCP config format
            fastmcp_config = {
                "mcpServers": {
                    self.name: {
                        "command": self.config["command"],
                        "args": self.config.get("args", []),
                    }
                }
            }
            
            logger.info(f"Creating FastMCP client for {self.name}...")
            
            # Create FastMCP Client with configuration
            self.client = Client(fastmcp_config)
            
            # Connect using async context manager
            await self.client.__aenter__()
            
            logger.info(f"Connected to {self.name}, discovering tools...")
            
            # Discover tools
            await self._discover_tools()
            
            logger.info(f"Successfully connected to {self.name} with {len(self._tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}", exc_info=True)
            return False
    
    async def _discover_tools(self) -> None:
        """Discover available tools from the MCP server."""
        try:
            if not self.client:
                return
            
            # List tools using FastMCP Client
            tools = await self.client.list_tools()
            
            self._tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                    "server": self.name
                }
                for tool in tools
            ]
            
            logger.info(f"Discovered {len(self._tools)} tools from {self.name}")
            logger.info(f"First 5 tool names: {[t['name'] for t in self._tools[:5]]}")
            logger.debug(f"All tools: {[t['name'] for t in self._tools]}")
            
        except Exception as e:
            logger.error(f"Failed to discover tools from {self.name}: {e}")
            self._tools = []
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools.
        
        Returns:
            List of tool definitions
        """
        return self._tools.copy()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        try:
            if not self.client:
                raise RuntimeError(f"Not connected to server {self.name}")
            
            logger.info(f"Calling tool {tool_name} on {self.name}")
            logger.debug(f"Arguments: {arguments}")
            
            # Call tool using FastMCP Client
            # Since we create a separate client per server, don't prefix the tool name
            result = await self.client.call_tool(tool_name, arguments)
            
            logger.debug(f"Tool {tool_name} result: {result}")
            
            # Extract text content from result
            content_text = ""
            if hasattr(result, 'content') and result.content:
                for item in result.content:
                    if hasattr(item, 'text'):
                        content_text += item.text
            
            return {
                "success": True,
                "result": content_text or str(result),
                "server": self.name,
                "tool": tool_name
            }
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {self.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "server": self.name,
                "tool": tool_name
            }
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        try:
            if self.client:
                await self.client.__aexit__(None, None, None)
                self.client = None
                logger.info(f"Disconnected from {self.name}")
        except Exception as e:
            logger.error(f"Error disconnecting from {self.name}: {e}")


class MCPManager:
    """Manager for multiple MCP servers."""
    
    def __init__(self, mcp_config: Dict[str, Dict[str, Any]]):
        """
        Initialize MCP manager.
        
        Args:
            mcp_config: Dictionary of MCP server configurations
        """
        self.mcp_config = mcp_config
        self.clients: Dict[str, MCPClient] = {}
    
    async def connect_all(self) -> None:
        """Connect to all MCP servers."""
        logger.info("Connecting to all MCP servers...")
        
        for name, config in self.mcp_config.items():
            client = MCPClient(name, config)
            success = await client.connect()
            if success:
                self.clients[name] = client
        
        logger.info(f"Connected to {len(self.clients)} MCP servers")
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all tools from all connected MCP servers.
        
        Returns:
            List of all available tools
        """
        all_tools = []
        for client in self.clients.values():
            all_tools.extend(client.get_tools())
        
        logger.info(f"Total tools available: {len(all_tools)}")
        return all_tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on a specific MCP server.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if server_name not in self.clients:
            return {
                "success": False,
                "error": f"Server {server_name} not connected",
                "server": server_name,
                "tool": tool_name
            }
        
        return await self.clients[server_name].call_tool(tool_name, arguments)
    
    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        logger.info("Disconnecting from all MCP servers...")
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()


@asynccontextmanager
async def create_mcp_manager(mcp_config: Dict[str, Dict[str, Any]]):
    """
    Context manager for MCP manager lifecycle.
    
    Args:
        mcp_config: MCP server configurations
        
    Yields:
        MCPManager instance
    """
    manager = MCPManager(mcp_config)
    try:
        await manager.connect_all()
        yield manager
    finally:
        await manager.disconnect_all()
