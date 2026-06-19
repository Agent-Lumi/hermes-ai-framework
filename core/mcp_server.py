"""
Hermes AI Framework - MCP Server
Model Context Protocol server implementation
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .config_models import MCPServerConfig, ToolConfig
from .logger import get_logger


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None


class MCPServer:
    """
    Model Context Protocol Server
    Exposes tools and resources to agents via MCP
    """
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, Any] = {}
        self.is_running = False
        self.logger = get_logger().get_server_logger(config.name)
    
    def register_tool(self, name: str, handler: Callable) -> None:
        """Register a tool handler"""
        self.tools[name] = handler
        print(f"Registered tool: {name}")
    
    def register_resource(self, name: str, data: Any) -> None:
        """Register a resource"""
        self.resources[name] = data
        print(f"Registered resource: {name}")
    
    async def start(self) -> None:
        """Start the MCP server"""
        self.is_running = True
        
        if self.config.transport == "stdio":
            await self._start_stdio()
        elif self.config.transport == "sse":
            await self._start_sse()
        elif self.config.transport == "websocket":
            await self._start_websocket()
        else:
            raise ValueError(f"Unknown transport: {self.config.transport}")
    
    async def stop(self) -> None:
        """Stop the MCP server"""
        self.is_running = False
        print(f"MCP Server '{self.config.name}' stopped")
    
    async def _start_stdio(self) -> None:
        """Start with stdio transport (for MCP CLI)"""
        print(f"MCP Server '{self.config.name}' started (stdio)")
        print(f"Tools available: {list(self.tools.keys())}")
        
        # In stdio mode, read from stdin and write to stdout
        import sys
        
        while self.is_running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                request = json.loads(line)
                response = await self._handle_request(request)
                
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                print(json.dumps({"error": f"Invalid JSON: {e}"}), flush=True)
            except Exception as e:
                print(json.dumps({"error": str(e)}), flush=True)
    
    async def _start_sse(self) -> None:
        """Start with Server-Sent Events transport"""
        from aiohttp import web
        
        app = web.Application()
        app.router.add_get('/tools', self._tools_handler)
        app.router.add_post('/invoke', self._invoke_handler)
        app.router.add_get('/resources/{name}', self._resource_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', 8081)
        await site.start()
        
        print(f"MCP Server '{self.config.name}' started (SSE on port 8081)")
        
        # Keep running
        while self.is_running:
            await asyncio.sleep(1)
        
        await runner.cleanup()
    
    async def _start_websocket(self) -> None:
        """Start with WebSocket transport"""
        import websockets
        
        async def handle_ws(websocket, path):
            async for message in websocket:
                try:
                    request = json.loads(message)
                    response = await self._handle_request(request)
                    await websocket.send(json.dumps(response))
                except Exception as e:
                    await websocket.send(json.dumps({"error": str(e)}))
        
        print(f"MCP Server '{self.config.name}' started (WebSocket on port 8082)")
        
        async with websockets.serve(handle_ws, '0.0.0.0', 8082):
            while self.is_running:
                await asyncio.sleep(1)
    
    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request"""
        method = request.get('method')
        
        if method == 'tools/list':
            return await self._list_tools()
        elif method == 'tools/invoke':
            return await self._invoke_tool(request.get('params', {}))
        elif method == 'resources/list':
            return await self._list_resources()
        elif method == 'resources/get':
            return await self._get_resource(request.get('params', {}))
        else:
            return {"error": f"Unknown method: {method}"}
    
    async def _list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        tools = []
        for tool_config in self.config.tools:
            tools.append({
                "name": tool_config.name,
                "description": tool_config.description,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required
                    }
                    for p in tool_config.parameters
                ]
            })
        
        return {
            "tools": tools,
            "count": len(tools)
        }
    
    async def _invoke_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a tool"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if not tool_name:
            return {"error": "Tool name required"}
        
        # Find tool
        tool_config = None
        for tc in self.config.tools:
            if tc.name == tool_name:
                tool_config = tc
                break
        
        if not tool_config:
            return {"error": f"Tool '{tool_name}' not found"}
        
        # Check if handler registered
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' handler not registered"}
        
        # Time the execution
        start_time = time.time()
        
        try:
            # Execute handler
            result = await self.tools[tool_name](**arguments)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the tool call
            from .logger import get_logger
            get_logger().log_mcp_call(
                self.config.name,
                tool_name,
                arguments,
                result,
                duration_ms
            )
            
            self.logger.info(f"Tool '{tool_name}' executed in {duration_ms:.2f}ms")
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the error
            from .logger import get_logger
            get_logger().log_mcp_call(
                self.config.name,
                tool_name,
                arguments,
                {"error": str(e)},
                duration_ms
            )
            
            self.logger.error(f"Tool '{tool_name}' failed after {duration_ms:.2f}ms: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        return {
            "resources": [
                {"name": name, "type": type(data).__name__}
                for name, data in self.resources.items()
            ]
        }
    
    async def _get_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a resource"""
        name = params.get('name')
        
        if name not in self.resources:
            return {"error": f"Resource '{name}' not found"}
        
        return {
            "success": True,
            "data": self.resources[name]
        }
    
    # HTTP handlers for SSE transport
    
    async def _tools_handler(self, request):
        """HTTP handler for listing tools"""
        from aiohttp import web
        result = await self._list_tools()
        return web.json_response(result)
    
    async def _invoke_handler(self, request):
        """HTTP handler for invoking tools"""
        from aiohttp import web
        params = await request.json()
        result = await self._invoke_tool(params)
        return web.json_response(result)
    
    async def _resource_handler(self, request):
        """HTTP handler for resources"""
        from aiohttp import web
        name = request.match_info['name']
        result = await self._get_resource({'name': name})
        return web.json_response(result)
    
    def get_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "transport": self.config.transport,
            "tools": [t.name for t in self.config.tools],
            "resources": list(self.resources.keys()),
            "is_running": self.is_running
        }
