"""
Standalone AutoGen Agent with File Operations and MCP Integration.
Uses Anthropic Vertex AI (not API key).

This agent can:
1. Read and write files
2. Interact with MCP servers (like Harness)
3. Use Claude via Vertex AI

Example usage:
    python agent.py "List all files and write them to files.txt"
"""
import asyncio
import os
import json
from typing import List, Optional

from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from autogen_core.model_context import BufferedChatCompletionContext

from file_tools import read_file, write_file, append_to_file, list_directory
from mcp_client import MCPClient
from vertex_client import create_vertex_client

from dotenv import load_dotenv


class FileAndMCPAgent:
    """
    Agent that combines file operations and MCP server tools.
    Uses Anthropic Vertex AI.
    """
    
    def __init__(
        self,
        name: str = "FileAgent",
        model: str = None,
        project_id: str = None,
        region: str = None,
        enable_mcp: bool = False,
        mcp_config: Optional[dict] = None,
        debug: bool = True,
    ):
        """
        Initialize the agent.
        
        Args:
            name: Name of the agent
            model: Model to use (default: from ANTHROPIC_VERTEX_MODEL env var)
            project_id: GCP project ID (default: from ANTHROPIC_VERTEX_GCP_PROJECT_ID env var)
            region: GCP region (default: from ANTHROPIC_VERTEX_GCP_REGION env var)
            enable_mcp: Whether to enable MCP integration
            mcp_config: Configuration for MCP server
            debug: Whether to enable debug logging
        """
        self.name = name
        self.model = model or os.getenv("ANTHROPIC_VERTEX_MODEL", "claude-sonnet-4-5@20250929")
        self.project_id = project_id or os.getenv("ANTHROPIC_VERTEX_GCP_PROJECT_ID")
        self.region = region or os.getenv("ANTHROPIC_VERTEX_GCP_REGION", "us-east5")
        self.enable_mcp = enable_mcp
        self.mcp_config = mcp_config
        self.mcp_client: Optional[MCPClient] = None
        self.agent: Optional[AssistantAgent] = None
        self.debug = debug
        self._model_client = None
        
        if not self.project_id:
            raise ValueError(
                "ANTHROPIC_VERTEX_GCP_PROJECT_ID not found. Set it as environment variable or pass to constructor."
            )
        
    async def initialize(self):
        """Initialize the agent and connect to MCP if enabled."""
        # Initialize MCP first if enabled
        if self.enable_mcp and self.mcp_config:
            await self._initialize_mcp()
        
        # Create model client
        self._model_client = create_vertex_client(
            model=self.model,
            project_id=self.project_id,
            region=self.region,
        )
        
        # Wrap the model client to log prompts and responses if debug is enabled
        if self.debug:
            original_create = self._model_client.create
            
            def _serialize_tools(tool_specs):
                """Serialize tools to show what the model actually sees."""
                if not tool_specs:
                    return []
                    
                serialized = []
                for t in tool_specs:
                    # AutoGen FunctionTool has a schema property that contains the tool definition
                    if hasattr(t, 'schema'):
                        serialized.append(t.schema)
                    elif isinstance(t, dict):
                        serialized.append(t)
                    else:
                        # Fallback: convert to string representation
                        serialized.append(str(t))
                return serialized
            
            async def logged_create(*args, **kwargs):
                # Log the exact payload being sent to Claude
                print("\n" + "=" * 80)
                print("FULL PROMPT SENT TO CLAUDE:")
                print("=" * 80)
                
                # Debug: Print all kwargs keys to see what's being passed
                print(f"DEBUG: kwargs keys = {list(kwargs.keys())}")
                print(f"DEBUG: args = {args}")
                
                # Extract and serialize tools properly
                tools = kwargs.get("tools", [])
                serialized_tools = _serialize_tools(tools) if tools else []
                
                # Get messages - check multiple possible keys
                messages = kwargs.get("messages", [])
                if not messages:
                    # Sometimes it might be in a different key
                    messages = kwargs.get("prompt", [])
                if not messages and args:
                    # Or maybe in args
                    messages = args[0] if args else []
                
                print(f"DEBUG: Found {len(messages)} messages")
                
                # Build the complete payload
                payload = {
                    "model": kwargs.get("model", "not specified"),
                    "messages": messages,
                    "tools": serialized_tools,
                }
                
                # Add any other parameters that are present
                for key in ["max_tokens", "temperature", "system", "tool_choice", "top_p", "stop_sequences"]:
                    if key in kwargs and kwargs[key] is not None:
                        payload[key] = kwargs[key]
                
                # Pretty print the complete payload
                print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
                print("=" * 80 + "\n")
                
                # Call the actual client
                result = await original_create(*args, **kwargs)
                
                # Log the response
                print("\n" + "=" * 80)
                print("AI RESPONSE:")
                print("=" * 80)
                print(json.dumps(result, indent=2, default=str))
                print("=" * 80 + "\n")
                
                return result
            
            self._model_client.create = logged_create
        
        # Create agent with proper configuration for multi-turn
        self.agent = AssistantAgent(
            name=self.name,
            model_client=self._model_client,
            tools=self._create_tools(),
            description="An assistant that can read/write files and interact with external services.",
            system_message="""You are a helpful assistant that can:
1. Read and write files on the local filesystem
2. List directory contents
3. Call Harness MCP tools using the call_harness_tool function

When working with Harness:
- Use call_harness_tool(tool_name, org_id, project_id, **params) to call any Harness tool
- For listing connectors: call_harness_tool("list_connectors", org_id="default", project_id="")
- For listing pipelines: call_harness_tool("list_pipelines", org_id="default", project_id="")
- For getting pipeline details: call_harness_tool("get_pipeline", org_id="default", project_id="", pipeline_id="...")
- For listing services: call_harness_tool("list_services", org_id="default", project_id="")

IMPORTANT: When asked to perform multi-step tasks:
- Execute steps sequentially and use tool results to inform next steps
- If asked to "list X and write to file Y":
  1. First call the appropriate tool to get the data
  2. Then call write_file() with the results from step 1
  3. Confirm both operations completed successfully
- Use tool results appropriately
- Provide clear feedback about what you're doing at each step

Always confirm successful operations and provide relevant details about what was accomplished.""",
            reflect_on_tool_use=False,
            model_client_stream=False,
            max_tool_iterations=20,  # Allow up to 20 tool calls
            model_context=BufferedChatCompletionContext(25),  # Buffer last 25 messages
        )
            
        print(f"Agent '{self.name}' initialized with model '{self.model}'")
    
    def _create_tools(self) -> List[FunctionTool]:
        """Create the list of tools for the agent."""
        tools = [
            FunctionTool(read_file, description="Read contents of a file"),
            FunctionTool(write_file, description="Write content to a file"),
            FunctionTool(append_to_file, description="Append content to a file"),
            FunctionTool(list_directory, description="List contents of a directory"),
        ]
        
        # Add MCP caller tool if MCP is enabled
        if self.enable_mcp:
            # Use self reference in closure
            agent_self = self
            
            async def call_harness_tool(
                tool_name: str,
                org_id: str = "default",
                project_id: str = "",
                pipeline_id: str = "",
                service_id: str = "",
                environment_id: str = "",
                execution_id: str = ""
            ) -> str:
                """
                Call a Harness MCP tool.
                
                Args:
                    tool_name: Name of the Harness tool to call (e.g., 'list_pipelines')
                    org_id: Harness organization ID (default: 'default')
                    project_id: Harness project ID (optional)
                    pipeline_id: Pipeline identifier (optional)
                    service_id: Service identifier (optional)
                    environment_id: Environment identifier (optional)
                    execution_id: Execution identifier (optional)
                """
                if not agent_self.mcp_client:
                    return "Error: MCP client not initialized"
                
                try:
                    # Build params dict
                    params = {}
                    if org_id:
                        params["org_id"] = org_id
                    if project_id:
                        params["project_id"] = project_id
                    if pipeline_id:
                        params["pipeline_id"] = pipeline_id
                    if service_id:
                        params["service_id"] = service_id
                    if environment_id:
                        params["environment_id"] = environment_id
                    if execution_id:
                        params["execution_id"] = execution_id
                    
                    result = await agent_self.mcp_client.call_tool(tool_name, params)
                    return str(result)
                except Exception as e:
                    error_msg = f"Error calling {tool_name}: {str(e)}"
                    return error_msg
            
            tools.append(
                FunctionTool(
                    call_harness_tool,
                    description="Call a Harness MCP tool by name with parameters"
                )
            )
        
        return tools
    
    async def _initialize_mcp(self):
        """Initialize MCP client."""
        try:
            self.mcp_client = MCPClient(self.mcp_config)
            await self.mcp_client.connect()
            
            available_tools = self.mcp_client.get_available_tools()
            print(f"Loaded {len(available_tools)} MCP tools")
            
        except Exception as e:
            print(f"Failed to initialize MCP: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def run(self, task: str) -> str:
        """
        Run the agent with a given task.
        Uses streaming to handle multi-turn conversations automatically.
        
        Args:
            task: The task description for the agent
            
        Returns:
            The agent's final response
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            if self.mcp_client:
                available_tools = self.mcp_client.get_available_tools()
                tool_list = ", ".join(available_tools[:30])
                if len(available_tools) > 30:
                    tool_list += f", and {len(available_tools) - 30} more"
                
                enhanced_task = f"""{task}

Note: {len(available_tools)} Harness MCP tools available including: {tool_list}
Use call_harness_tool(tool_name, org_id="default", project_id="", **params) to call any tool."""
            else:
                enhanced_task = task
            
            # Create the initial message
            initial_message = TextMessage(content=enhanced_task, source="user")
            
            # Use run_stream to handle the full conversation including tool execution
            # AutoGen will automatically handle multi-turn tool calling
            cancellation_token = CancellationToken()
            
            # Collect the final text response
            final_response = None
            executed_tool_ids = set()  # Guard 2: Track executed tool call IDs
            
            # Stream through all events
            async for message in self.agent.on_messages_stream([initial_message], cancellation_token):
                # Process different event types
                if not hasattr(message, 'type'):
                    continue
                    
                event_type = message.type
                
                # Guard 2: De-duplicate tool calls by tracking tool_use IDs
                if event_type == "ToolCallRequestEvent":
                    if hasattr(message, 'content'):
                        for call in message.content:
                            if hasattr(call, 'id'):
                                tool_id = call.id
                                if tool_id in executed_tool_ids:
                                    # Duplicate tool call detected, skip
                                    continue
                                executed_tool_ids.add(tool_id)
                
                # Look for final TextMessage from the assistant
                if event_type == "TextMessage":
                    if hasattr(message, 'source') and message.source != "user":
                        if hasattr(message, 'content') and isinstance(message.content, str):
                            final_response = message.content
                
                # Guard 1: Check for stop/finish conditions
                # Check if this message indicates completion (stop_reason or finish_reason)
                if hasattr(message, 'stop_reason') and message.stop_reason in ['stop', 'end_turn']:
                    break
                if hasattr(message, 'finish_reason') and message.finish_reason in ['stop', 'end_turn']:
                    break
                    
            # Guard 3: Don't call on_messages() after the loop - just return
            if final_response:
                return final_response
            
            # If no response from stream, return error
            return "No response received from agent"
                
        except Exception as e:
            print(f"Error running agent: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    async def cleanup(self):
        """Clean up resources."""
        if self.mcp_client:
            await self.mcp_client.disconnect()
        
        if self._model_client:
            await self._model_client.close()


async def main():
    """Example usage of the agent."""
    load_dotenv()
    
    print("\n" + "=" * 70)
    print("AutoGen Agent with File Operations & MCP Integration")
    print("Using Anthropic Vertex AI")
    print("=" * 70 + "\n")
    
    print("Example 1: File Operations\n")
    
    agent = FileAndMCPAgent(name="FileAgent", debug=True)
    await agent.initialize()
    
    task1 = "Create a file called 'test_output.txt' and write 'Hello from AutoGen with Vertex AI!' to it. Then create another file called test_output2.txt, read the content of requirements.txt in current directory and write it to test_output2.txt"
    print(f"Task: {task1}")
    response = await agent.run(task1)
    print(f"\nFinal Response: {response}\n")
    
    await agent.cleanup()
    
    print("\n" + "=" * 70)
    print("Example 2: Harness MCP Integration")
    print("=" * 70 + "\n")
    
    binary_path = os.getenv("HARNESS_MCP_BINARY")
    api_key = os.getenv("HARNESS_API_KEY")
    
    if not binary_path or not api_key:
        print("Skipping Harness example: HARNESS_MCP_BINARY and HARNESS_API_KEY not set")
        print("Download binary from: https://github.com/harness/mcp-server/releases\n")
        return
    
    if not os.path.exists(binary_path):
        print(f"Binary not found: {binary_path}")
        print("Download from: https://github.com/harness/mcp-server/releases\n")
        return
    
    if not binary_path.endswith('.exe'):
        try:
            os.chmod(binary_path, 0o755)
        except Exception:
            pass
    
    base_url = os.getenv("HARNESS_BASE_URL", "https://app.harness.io")
    org_id = os.getenv("HARNESS_DEFAULT_ORG_ID", "default")
    project_id = os.getenv("HARNESS_DEFAULT_PROJECT_ID")
    
    mcp_config = {
        "command": binary_path,
        "args": ["stdio", "--toolsets=all"],
        "env": {
            "HARNESS_API_KEY": api_key,
            "HARNESS_BASE_URL": base_url,
            "HARNESS_TOOLSETS": "all",
            "HARNESS_READ_ONLY": "false",
        }
    }
    
    if org_id:
        mcp_config["env"]["HARNESS_DEFAULT_ORG_ID"] = org_id
    if project_id:
        mcp_config["env"]["HARNESS_DEFAULT_PROJECT_ID"] = project_id
    
    agent_with_mcp = FileAndMCPAgent(
        name="HarnessAgent",
        enable_mcp=True,
        mcp_config=mcp_config,
        debug=True
    )
    
    try:
        await agent_with_mcp.initialize()
        
        task = "List all connectors and write them to a file called 'connectors.txt'. Make sure to complete both steps."
        print(f"Task: {task}")
        response = await agent_with_mcp.run(task)
        print(f"\nFinal Response: {response}\n")
            
    except Exception as e:
        print(f"Harness MCP example failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await agent_with_mcp.cleanup()
    
    print("=" * 70)
    print("Done!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        
        async def run_task():
            load_dotenv()
            agent = FileAndMCPAgent(name="FileAgent", debug=True)
            await agent.initialize()
            print(f"\nTask: {task}\n")
            response = await agent.run(task)
            print(f"\nFinal Response:\n{response}\n")
            await agent.cleanup()
        
        asyncio.run(run_task())
    else:
        asyncio.run(main())
