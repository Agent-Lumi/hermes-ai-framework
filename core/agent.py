"""
Hermes AI Framework - Agent Implementation
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .config_models import AgentConfig, MemoryConfig
from .providers import BaseProvider, ProviderFactory


class AgentMemory:
    """Manages agent conversation memory"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.messages: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str, **metadata) -> None:
        """Add a message to memory"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        self.messages.append(message)
        
        # Trim if needed
        if self.config.max_messages and len(self.messages) > self.config.max_messages:
            self.messages = self.messages[-self.config.max_messages:]
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get messages for context"""
        msgs = self.messages
        if limit:
            msgs = msgs[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in msgs]
    
    def clear(self) -> None:
        """Clear all memory"""
        self.messages = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get full message history"""
        return self.messages


class Agent:
    """
    Hermes AI Agent
    An autonomous agent with configurable capabilities
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.memory = AgentMemory(config.memory)
        self.provider: Optional[BaseProvider] = None
        self.is_running = False
        
        # Initialize provider
        self._init_provider()
    
    def _init_provider(self) -> None:
        """Initialize the AI provider"""
        try:
            self.provider = ProviderFactory.create(self.config.provider)
            print(f"Initialized {self.config.provider.name} provider for agent '{self.config.name}'")
        except Exception as e:
            print(f"Failed to initialize provider: {e}")
    
    async def health_check(self) -> bool:
        """Check if agent is healthy"""
        if not self.provider:
            return False
        return await self.provider.health_check()
    
    async def chat(self, message: str, **kwargs) -> str:
        """
        Send a message to the agent and get a response
        
        Args:
            message: User message
            **kwargs: Additional parameters
            
        Returns:
            Agent response
        """
        if not self.provider:
            return "Error: Provider not initialized"
        
        # Build messages
        messages = []
        
        # Add system prompt
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt
            })
        
        # Add memory context
        memory_msgs = self.memory.get_messages(self.config.memory.max_messages)
        messages.extend(memory_msgs)
        
        # Add user message
        messages.append({"role": "user", "content": message})
        
        # Get response
        try:
            response = await self.provider.chat(messages, **kwargs)
            
            # Store in memory
            self.memory.add_message("user", message)
            self.memory.add_message("assistant", response, message_id=len(self.memory.messages))
            
            return response
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def chat_stream(self, message: str, **kwargs):
        """
        Send a message and stream the response
        
        Yields response chunks as they arrive
        """
        if not self.provider:
            yield "Error: Provider not initialized"
            return
        
        # Build messages
        messages = []
        
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt
            })
        
        memory_msgs = self.memory.get_messages(self.config.memory.max_messages)
        messages.extend(memory_msgs)
        messages.append({"role": "user", "content": message})
        
        # Store user message
        self.memory.add_message("user", message)
        
        # Collect full response
        full_response = []
        
        try:
            async for chunk in self.provider.chat_stream(messages, **kwargs):
                full_response.append(chunk)
                yield chunk
            
            # Store complete response
            self.memory.add_message(
                "assistant", 
                ''.join(full_response),
                message_id=len(self.memory.messages)
            )
            
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_memory(self) -> List[Dict[str, Any]]:
        """Get conversation memory"""
        return self.memory.get_history()
    
    def clear_memory(self) -> None:
        """Clear conversation memory"""
        self.memory.clear()
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "provider": self.config.provider.name,
            "model": self.config.provider.model,
            "capabilities": self.config.capabilities,
            "memory_count": len(self.memory.messages),
            "is_running": self.is_running
        }
    
    async def start(self) -> None:
        """Start the agent"""
        if not await self.health_check():
            raise Exception("Agent failed health check")
        
        self.is_running = True
        print(f"Agent '{self.config.name}' started")
    
    async def stop(self) -> None:
        """Stop the agent"""
        self.is_running = False
        print(f"Agent '{self.config.name}' stopped")


class AgentManager:
    """Manages multiple agents"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
    
    def create_agent(self, config: AgentConfig) -> Agent:
        """Create and register a new agent"""
        agent = Agent(config)
        self.agents[config.name] = agent
        return agent
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name"""
        return self.agents.get(name)
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent"""
        if name in self.agents:
            del self.agents[name]
            return True
        return False
    
    def list_agents(self) -> List[str]:
        """List all agent names"""
        return list(self.agents.keys())
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all agents"""
        results = {}
        for name, agent in self.agents.items():
            results[name] = await agent.health_check()
        return results
