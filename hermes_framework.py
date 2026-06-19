"""
Hermes AI Framework - Main Entry Point
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict

from core.config_manager import ConfigManager
from core.agent import AgentManager
from core.a2a_server import A2AServer
from core.mcp_server import MCPServer


class HermesFramework:
    """
    Main Hermes AI Framework class
    Manages agents, A2A servers, and MCP servers
    """
    
    def __init__(self, config_dir: str = "./configs"):
        self.config_dir = Path(config_dir)
        self.config_manager = ConfigManager(config_dir)
        self.agent_manager = AgentManager()
        self.a2a_servers: Dict[str, A2AServer] = {}
        self.mcp_servers: Dict[str, MCPServer] = {}
    
    async def initialize(self) -> None:
        """Initialize the framework"""
        print("=" * 60)
        print("Hermes AI Framework")
        print("=" * 60)
        
        # Load configurations
        print("\nLoading configurations...")
        self.config_manager.load_all()
        
        # Initialize agents
        print("\nInitializing agents...")
        for name, config in self.config_manager.agents.items():
            self.agent_manager.create_agent(config)
            print(f"  ✓ Agent: {name}")
        
        print("\nFramework initialized!")
    
    async def start(self) -> None:
        """Start all services"""
        print("\nStarting services...")
        
        # Start agents
        for name, agent in self.agent_manager.agents.items():
            try:
                await agent.start()
                print(f"  ✓ Agent '{name}' started")
            except Exception as e:
                print(f"  ✗ Agent '{name}' failed: {e}")
        
        # Start A2A servers
        for name, config in self.config_manager.a2a_servers.items():
            try:
                server = A2AServer(config)
                await server.start()
                self.a2a_servers[name] = server
                print(f"  ✓ A2A Server '{name}' started")
            except Exception as e:
                print(f"  ✗ A2A Server '{name}' failed: {e}")
        
        # Start MCP servers
        for name, config in self.config_manager.mcp_servers.items():
            try:
                server = MCPServer(config)
                await server.start()
                self.mcp_servers[name] = server
                print(f"  ✓ MCP Server '{name}' started")
            except Exception as e:
                print(f"  ✗ MCP Server '{name}' failed: {e}")
        
        print("\nAll services started!")
        print("Press Ctrl+C to stop\n")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
    
    async def stop(self) -> None:
        """Stop all services"""
        print("Stopping services...")
        
        # Stop agents
        for name, agent in self.agent_manager.agents.items():
            await agent.stop()
        
        # Stop A2A servers
        for name, server in self.a2a_servers.items():
            await server.stop()
        
        # Stop MCP servers
        for name, server in self.mcp_servers.items():
            await server.stop()
        
        print("All services stopped!")
    
    def get_status(self) -> dict:
        """Get framework status"""
        return {
            "agents": {
                name: agent.get_info()
                for name, agent in self.agent_manager.agents.items()
            },
            "a2a_servers": {
                name: server.get_info()
                for name, server in self.a2a_servers.items()
            },
            "mcp_servers": {
                name: server.get_info()
                for name, server in self.mcp_servers.items()
            }
        }


async def main():
    """Main entry point"""
    framework = HermesFramework()
    
    try:
        await framework.initialize()
        await framework.start()
    except KeyboardInterrupt:
        pass
    finally:
        await framework.stop()


if __name__ == "__main__":
    asyncio.run(main())
