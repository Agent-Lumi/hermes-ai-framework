"""
Hermes AI Framework - Configuration Manager
Handles loading and validation of YAML configurations
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Type, Union
from pydantic import ValidationError

from .config_models import (
    AgentConfig,
    A2AServerConfig,
    MCPServerConfig,
    ProviderConfigUnion
)


class ConfigManager:
    """Manages framework configurations"""
    
    def __init__(self, config_dir: str = "./configs"):
        self.config_dir = Path(config_dir)
        self.agents: Dict[str, AgentConfig] = {}
        self.a2a_servers: Dict[str, A2AServerConfig] = {}
        self.mcp_servers: Dict[str, MCPServerConfig] = {}
        self.providers: Dict[str, ProviderConfigUnion] = {}
    
    def load_all(self) -> None:
        """Load all configurations from the config directory"""
        self._load_agents()
        self._load_a2a_servers()
        self._load_mcp_servers()
        self._load_providers()
    
    def _load_yaml(self, path: Path) -> Optional[dict]:
        """Load a YAML file"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None
    
    def _load_agents(self) -> None:
        """Load all agent configurations"""
        agents_dir = self.config_dir / "agents"
        if not agents_dir.exists():
            return
        
        for yaml_file in agents_dir.glob("*.yaml"):
            data = self._load_yaml(yaml_file)
            if data:
                try:
                    config = AgentConfig(**data)
                    self.agents[config.name] = config
                    print(f"Loaded agent: {config.name}")
                except ValidationError as e:
                    print(f"Invalid agent config {yaml_file}: {e}")
    
    def _load_a2a_servers(self) -> None:
        """Load all A2A server configurations"""
        a2a_dir = self.config_dir / "a2a_servers"
        if not a2a_dir.exists():
            return
        
        for yaml_file in a2a_dir.glob("*.yaml"):
            data = self._load_yaml(yaml_file)
            if data:
                try:
                    config = A2AServerConfig(**data)
                    self.a2a_servers[config.name] = config
                    print(f"Loaded A2A server: {config.name}")
                except ValidationError as e:
                    print(f"Invalid A2A config {yaml_file}: {e}")
    
    def _load_mcp_servers(self) -> None:
        """Load all MCP server configurations"""
        mcp_dir = self.config_dir / "mcp_servers"
        if not mcp_dir.exists():
            return
        
        for yaml_file in mcp_dir.glob("*.yaml"):
            data = self._load_yaml(yaml_file)
            if data:
                try:
                    config = MCPServerConfig(**data)
                    self.mcp_servers[config.name] = config
                    print(f"Loaded MCP server: {config.name}")
                except ValidationError as e:
                    print(f"Invalid MCP config {yaml_file}: {e}")
    
    def _load_providers(self) -> None:
        """Load all provider configurations"""
        providers_dir = self.config_dir / "providers"
        if not providers_dir.exists():
            return
        
        for yaml_file in providers_dir.glob("*.yaml"):
            data = self._load_yaml(yaml_file)
            if data:
                try:
                    # Provider configs don't have a unified model yet
                    self.providers[data.get('name', yaml_file.stem)] = data
                    print(f"Loaded provider: {data.get('name', yaml_file.stem)}")
                except Exception as e:
                    print(f"Invalid provider config {yaml_file}: {e}")
    
    def get_agent(self, name: str) -> Optional[AgentConfig]:
        """Get an agent configuration by name"""
        return self.agents.get(name)
    
    def get_a2a_server(self, name: str) -> Optional[A2AServerConfig]:
        """Get an A2A server configuration by name"""
        return self.a2a_servers.get(name)
    
    def get_mcp_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get an MCP server configuration by name"""
        return self.mcp_servers.get(name)
    
    def list_agents(self) -> List[str]:
        """List all loaded agent names"""
        return list(self.agents.keys())
    
    def list_a2a_servers(self) -> List[str]:
        """List all loaded A2A server names"""
        return list(self.a2a_servers.keys())
    
    def list_mcp_servers(self) -> List[str]:
        """List all loaded MCP server names"""
        return list(self.mcp_servers.keys())
    
    def validate_all(self) -> bool:
        """Validate all loaded configurations"""
        errors = []
        
        for name, config in self.agents.items():
            try:
                AgentConfig(**config.dict())
            except ValidationError as e:
                errors.append(f"Agent '{name}': {e}")
        
        for name, config in self.a2a_servers.items():
            try:
                A2AServerConfig(**config.dict())
            except ValidationError as e:
                errors.append(f"A2A server '{name}': {e}")
        
        for name, config in self.mcp_servers.items():
            try:
                MCPServerConfig(**config.dict())
            except ValidationError as e:
                errors.append(f"MCP server '{name}': {e}")
        
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("All configurations validated successfully!")
        return True
    
    def create_example_configs(self) -> None:
        """Create example configuration files"""
        # Ensure directories exist
        (self.config_dir / "agents").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "a2a_servers").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "mcp_servers").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "providers").mkdir(parents=True, exist_ok=True)
        
        # Create example agent
        example_agent = {
            "name": "code_assistant",
            "description": "A coding assistant for Python and SQL",
            "use_case": """
This agent assists with:
- Writing Python code
- SQL query optimization
- Code review and debugging
- Best practices guidance
            """.strip(),
            "provider": {
                "name": "ollama",
                "model": "llama3.2:latest",
                "server_url": "http://192.168.99.113:11434",
                "temperature": 0.7
            },
            "capabilities": [
                "code_generation",
                "code_review",
                "sql_optimization"
            ],
            "tools": ["python_executor", "sql_analyzer"],
            "memory": {
                "type": "conversation",
                "max_messages": 20
            },
            "output": {
                "format": "markdown",
                "streaming": True
            },
            "system_prompt": "You are a helpful coding assistant. Provide clear, concise code examples."
        }
        
        with open(self.config_dir / "agents" / "code_assistant.yaml", 'w') as f:
            yaml.dump(example_agent, f, default_flow_style=False, sort_keys=False)
        
        # Create example A2A server
        example_a2a = {
            "name": "hermes_hub",
            "description": "Central A2A communication hub",
            "use_case": """
Facilitates agent-to-agent communication:
- Routes messages between registered agents
- Provides agent discovery service
- Handles load balancing
            """.strip(),
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "protocol": "http"
            },
            "agents": ["code_assistant"],
            "features": {
                "discovery": True,
                "routing": True,
                "load_balancing": True
            }
        }
        
        with open(self.config_dir / "a2a_servers" / "hub.yaml", 'w') as f:
            yaml.dump(example_a2a, f, default_flow_style=False, sort_keys=False)
        
        # Create example MCP server
        example_mcp = {
            "name": "tool_registry",
            "description": "MCP server providing tool access",
            "use_case": """
Exposes tools via MCP protocol:
- Database queries
- Web scraping
- File operations
            """.strip(),
            "transport": "stdio",
            "tools": [
                {
                    "name": "database_query",
                    "description": "Execute SQL queries",
                    "parameters": [
                        {
                            "name": "connection_string",
                            "type": "string",
                            "description": "Database connection string",
                            "required": True
                        },
                        {
                            "name": "query",
                            "type": "string",
                            "description": "SQL query to execute",
                            "required": True
                        }
                    ]
                },
                {
                    "name": "web_scrape",
                    "description": "Scrape web content",
                    "parameters": [
                        {
                            "name": "url",
                            "type": "string",
                            "description": "URL to scrape",
                            "required": True
                        }
                    ]
                }
            ]
        }
        
        with open(self.config_dir / "mcp_servers" / "tools.yaml", 'w') as f:
            yaml.dump(example_mcp, f, default_flow_style=False, sort_keys=False)
        
        print(f"Example configs created in {self.config_dir}")
