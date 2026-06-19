"""
Hermes AI Framework - A2A Server
Agent-to-Agent communication server
"""
import asyncio
import json
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import aiohttp
from aiohttp import web

from .config_models import A2AServerConfig


@dataclass
class AgentRegistration:
    """Registered agent information"""
    name: str
    endpoint: str
    capabilities: List[str]
    last_seen: datetime = field(default_factory=datetime.now)
    is_online: bool = True


class A2AServer:
    """
    Agent-to-Agent communication server
    Facilitates message routing between agents
    """
    
    def __init__(self, config: A2AServerConfig):
        self.config = config
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.agents: Dict[str, AgentRegistration] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
    
    async def start(self) -> None:
        """Start the A2A server"""
        self.app = web.Application()
        self._setup_routes()
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(
            self.runner,
            self.config.server.get('host', '0.0.0.0'),
            self.config.server.get('port', 8000)
        )
        
        await site.start()
        self.is_running = True
        
        host = self.config.server.get('host', '0.0.0.0')
        port = self.config.server.get('port', 8000)
        print(f"A2A Server '{self.config.name}' started on http://{host}:{port}")
        
        # Start background tasks
        asyncio.create_task(self._health_check_loop())
    
    async def stop(self) -> None:
        """Stop the A2A server"""
        if self.runner:
            await self.runner.cleanup()
        self.is_running = False
        print(f"A2A Server '{self.config.name}' stopped")
    
    def _setup_routes(self) -> None:
        """Setup HTTP routes"""
        self.app.router.add_get('/health', self._health_handler)
        self.app.router.add_post('/register', self._register_handler)
        self.app.router.add_post('/unregister', self._unregister_handler)
        self.app.router.add_post('/send', self._send_message_handler)
        self.app.router.add_get('/agents', self._list_agents_handler)
        self.app.router.add_get('/discover', self._discover_handler)
    
    async def _health_handler(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "server": self.config.name,
            "registered_agents": len(self.agents),
            "online_agents": sum(1 for a in self.agents.values() if a.is_online)
        })
    
    async def _register_handler(self, request: web.Request) -> web.Response:
        """Register an agent"""
        try:
            data = await request.json()
            
            agent = AgentRegistration(
                name=data['name'],
                endpoint=data['endpoint'],
                capabilities=data.get('capabilities', [])
            )
            
            self.agents[agent.name] = agent
            
            print(f"Agent registered: {agent.name} at {agent.endpoint}")
            
            return web.json_response({
                "status": "registered",
                "agent": agent.name,
                "message": f"Welcome to {self.config.name}"
            })
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=400
            )
    
    async def _unregister_handler(self, request: web.Request) -> web.Response:
        """Unregister an agent"""
        try:
            data = await request.json()
            name = data.get('name')
            
            if name in self.agents:
                del self.agents[name]
                print(f"Agent unregistered: {name}")
                return web.json_response({"status": "unregistered"})
            
            return web.json_response(
                {"error": "Agent not found"},
                status=404
            )
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=400
            )
    
    async def _send_message_handler(self, request: web.Request) -> web.Response:
        """Send message from one agent to another"""
        try:
            data = await request.json()
            
            sender = data.get('sender')
            recipient = data.get('recipient')
            message = data.get('message')
            
            if not all([sender, recipient, message]):
                return web.json_response(
                    {"error": "Missing required fields: sender, recipient, message"},
                    status=400
                )
            
            # Check if recipient is registered
            if recipient not in self.agents:
                return web.json_response(
                    {"error": f"Recipient '{recipient}' not found"},
                    status=404
                )
            
            recipient_agent = self.agents[recipient]
            
            if not recipient_agent.is_online:
                return web.json_response(
                    {"error": f"Recipient '{recipient}' is offline"},
                    status=503
                )
            
            # Forward message
            success = await self._forward_message(
                sender,
                recipient_agent,
                message
            )
            
            if success:
                return web.json_response({
                    "status": "delivered",
                    "from": sender,
                    "to": recipient,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return web.json_response(
                    {"error": "Failed to deliver message"},
                    status=500
                )
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    
    async def _forward_message(self, sender: str, recipient: AgentRegistration, message: str) -> bool:
        """Forward a message to a recipient agent"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "sender": sender,
                    "recipient": recipient.name,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                async with session.post(
                    f"{recipient.endpoint}/receive",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"Failed to forward message to {recipient.name}: {e}")
            return False
    
    async def _list_agents_handler(self, request: web.Request) -> web.Response:
        """List registered agents"""
        agents_list = [
            {
                "name": agent.name,
                "endpoint": agent.endpoint,
                "capabilities": agent.capabilities,
                "is_online": agent.is_online,
                "last_seen": agent.last_seen.isoformat()
            }
            for agent in self.agents.values()
        ]
        
        return web.json_response({
            "agents": agents_list,
            "total": len(agents_list),
            "online": sum(1 for a in self.agents.values() if a.is_online)
        })
    
    async def _discover_handler(self, request: web.Request) -> web.Response:
        """Discover agents by capability"""
        capability = request.query.get('capability')
        
        matching = [
            {
                "name": agent.name,
                "endpoint": agent.endpoint,
                "capabilities": agent.capabilities
            }
            for agent in self.agents.values()
            if not capability or capability in agent.capabilities
        ]
        
        return web.json_response({
            "agents": matching,
            "capability_filter": capability
        })
    
    async def _health_check_loop(self) -> None:
        """Periodically check agent health"""
        while self.is_running:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            for agent in list(self.agents.values()):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{agent.endpoint}/health",
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            agent.is_online = response.status == 200
                            if agent.is_online:
                                agent.last_seen = datetime.now()
                                
                except Exception:
                    agent.is_online = False
                    print(f"Agent {agent.name} appears offline")
    
    def get_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "host": self.config.server.get('host', '0.0.0.0'),
            "port": self.config.server.get('port', 8000),
            "registered_agents": len(self.agents),
            "online_agents": sum(1 for a in self.agents.values() if a.is_online),
            "is_running": self.is_running
        }
