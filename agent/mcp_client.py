"""
MCP (Model Context Protocol) Client for integrating external tools.
This allows the agent to use MCP servers like Harness via stdio binary.
Based on working implementation from Harness MCP server.
"""
import asyncio
import json
from typing import Any, Dict, List, Optional, Annotated
from contextlib import AsyncExitStack

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import Tool, TextContent
except ImportError:
    print("Warning: mcp package not installed. Install with: pip install mcp")
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None
    Tool = None
    TextContent = None


class MCPClient:
    """
    Client for interacting with MCP servers via stdio (binary executable).
    Manages connection to MCP server and provides tool execution capabilities.
    
    Based on the working Harness MCP client implementation.
    """
    
    def __init__(self, server_config: Dict[str, Any]):
        """
        Initialize MCP client with server configuration.
        
        Args:
            server_config: Configuration for the MCP server
                Required format for Harness binary:
                {
                    "command": "/path/to/harness-mcp-server-binary",
                    "args": ["stdio", "--toolsets=all"],
                    "env": {
                        "HARNESS_API_KEY": "your_api_key",
                        "HARNESS_BASE_URL": "https://app.harness.io",
                        "HARNESS_TOOLSETS": "all",
                        "HARNESS_READ_ONLY": "false",
                        "HARNESS_DEFAULT_ORG_ID": "default",  # optional
                        "HARNESS_DEFAULT_PROJECT_ID": "project"  # optional
                    }
                }
        """
        if not all([ClientSession, StdioServerParameters, stdio_client]):
            raise ImportError(
                "MCP package not installed. Install with: pip install mcp"
            )
        
        self.server_config = server_config
        self.session: Optional[ClientSession] = None
        self.exit_stack: Optional[AsyncExitStack] = None
        self.available_tools: Dict[str, Tool] = {}
        self.stdio_connection = None
        self.connection_healthy = False
        self.last_heartbeat = None
    
    async def connect(self):
        """Establish connection to the MCP server via stdio."""
        if self.session:
            print("Already connected to MCP server")
            return
        
        try:
            self.exit_stack = AsyncExitStack()
            
            # Create server parameters for stdio connection
            # This matches the working Harness implementation
            server_params = StdioServerParameters(
                command=self.server_config["command"],
                args=self.server_config.get("args", ["stdio"]),
                env=self.server_config.get("env", {}),
            )
            
            print(f"🔌 Connecting to MCP server: {self.server_config['command']}")
            print(f"   Args: {self.server_config.get('args', [])}")
            
            # Connect to server via stdio
            self.stdio_connection = stdio_client(server_params)
            stdio_transport = await self.exit_stack.enter_async_context(
                self.stdio_connection
            )
            
            self.read, self.write = stdio_transport
            
            # Create session
            self.session = ClientSession(self.read, self.write)
            await self.exit_stack.enter_async_context(self.session)
            
            # Initialize session and discover tools
            await self._initialize_session()
            
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            await self.disconnect()
            raise
    
    async def _initialize_session(self):
        """Initialize the MCP session and discover available tools."""
        if not self.session:
            raise RuntimeError("Session not established")
        
        try:
            # Initialize the session
            await self.session.initialize()
            
            # List available tools
            tools_response = await self.session.list_tools()
            self.available_tools = {
                tool.name: tool for tool in tools_response.tools
            }
            
            # Mark connection as healthy
            self.connection_healthy = True
            self.last_heartbeat = asyncio.get_event_loop().time()
            
            print(f"✅ Connected to MCP server with {len(self.available_tools)} tools")
            print(f"   Available tools: {list(self.available_tools.keys())[:5]}...")
            if len(self.available_tools) > 5:
                print(f"   ... and {len(self.available_tools) - 5} more")
            
        except Exception as e:
            print(f"❌ Failed to initialize MCP session: {e}")
            raise
    
    async def heartbeat(self) -> bool:
        """Send a heartbeat to keep the connection alive."""
        if not self.session or not self.connection_healthy:
            return False
        
        try:
            # Use a lightweight operation to check connection health
            await self.session.list_tools()
            self.last_heartbeat = asyncio.get_event_loop().time()
            self.connection_healthy = True
            return True
        except Exception as e:
            print(f"⚠️  MCP heartbeat failed: {e}")
            self.connection_healthy = False
            return False
    
    async def disconnect(self):
        """Close connection to the MCP server."""
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                print(f"Warning during disconnect: {e}")
            finally:
                self.exit_stack = None
                self.session = None
                self.available_tools = {}
                self.stdio_connection = None
                self.connection_healthy = False
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.available_tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        tool = self.available_tools.get(tool_name)
        if not tool:
            return None
        
        # Extract input schema properly
        input_schema = {}
        if hasattr(tool, 'inputSchema'):
            input_schema = tool.inputSchema
        
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": input_schema,
        }
    
    async def call_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            The result from the tool execution
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")
        
        if tool_name not in self.available_tools:
            available = list(self.available_tools.keys())
            raise ValueError(
                f"Tool '{tool_name}' not available. "
                f"Available tools: {available[:10]}{'...' if len(available) > 10 else ''}"
            )
        
        try:
            print(f"🔧 Calling MCP tool: {tool_name}")
            if arguments:
                print(f"   Arguments: {arguments}")
            
            # Call the tool
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract content from result - matching working implementation
            response_data = []
            if hasattr(result, 'content') and result.content:
                for i, content in enumerate(result.content):
                    if isinstance(content, TextContent):
                        response_data.append(content.text)
                    elif hasattr(content, 'text'):
                        response_data.append(content.text)
                    else:
                        response_data.append(str(content))
            
            # Return combined response
            if len(response_data) == 1:
                return response_data[0]
            elif len(response_data) > 1:
                return "\n".join(response_data)
            else:
                return str(result)
            
        except Exception as e:
            print(f"❌ Error calling MCP tool {tool_name}: {e}")
            raise
    
    async def is_connected(self) -> bool:
        """Check if the client is properly connected."""
        return (self.session is not None and 
                self.connection_healthy and
                hasattr(self.session, '_read_stream') and 
                self.session._read_stream is not None)


# Create wrapper functions for AutoGen tools
def create_mcp_tool_wrapper(
    mcp_client: MCPClient,
    tool_name: str,
    tool_info: Dict[str, Any]
):
    """
    Create a wrapper function for an MCP tool that can be used with AutoGen.
    
    Args:
        mcp_client: The MCP client instance
        tool_name: Name of the tool
        tool_info: Information about the tool from MCP
        
    Returns:
        A function that can be registered with AutoGen
    """
    # Get input schema
    input_schema = tool_info.get("input_schema", {})
    properties = {}
    if isinstance(input_schema, dict):
        properties = input_schema.get("properties", {})
    elif hasattr(input_schema, "properties"):
        properties = input_schema.properties or {}
    
    # Create function with dynamic parameters based on schema
    param_names = list(properties.keys()) if properties else []
    
    # Build function signature dynamically
    if param_names:
        # Create parameters string for function definition
        params_str = ", ".join([f"{name}=None" for name in param_names])
        func_def = f"async def {tool_name}({params_str}):\n    pass"
        
        # Create namespace for exec
        namespace = {}
        exec(func_def, namespace)
        func = namespace[tool_name]
        
        # Replace implementation
        async def impl(**call_params):
            try:
                # Filter out None values
                filtered_params = {k: v for k, v in call_params.items() if v is not None}
                result = await mcp_client.call_tool(tool_name, filtered_params)
                return str(result)
            except Exception as e:
                error_msg = f"Error calling {tool_name}: {str(e)}"
                print(error_msg)
                return error_msg
        
        # Copy implementation to dynamically created function
        func.__code__ = impl.__code__
        func.__globals__.update({'mcp_client': mcp_client, 'tool_name': tool_name})
    else:
        # No parameters - simple function
        async def func():
            try:
                result = await mcp_client.call_tool(tool_name, {})
                return str(result)
            except Exception as e:
                error_msg = f"Error calling {tool_name}: {str(e)}"
                print(error_msg)
                return error_msg
        
        func.__name__ = tool_name
    
    # Set metadata
    func.__doc__ = tool_info.get("description", f"MCP tool: {tool_name}")
    
    return func