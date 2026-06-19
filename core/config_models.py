"""
Hermes AI Framework - Core Configuration Models
"""
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProviderType(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class CapabilityType(str, Enum):
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DATA_ANALYSIS = "data_analysis"
    WEB_RESEARCH = "web_research"
    SQL_OPTIMIZATION = "sql_optimization"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    CUSTOM = "custom"


# ============== Provider Configurations ==============

class ProviderConfig(BaseModel):
    """Base configuration for AI providers"""
    name: str = Field(..., description="Provider name (ollama, openai, etc.)")
    model: str = Field(..., description="Model identifier")
    server_url: Optional[str] = Field(None, description="Server URL for local providers")
    api_key: Optional[str] = Field(None, description="API key for cloud providers")
    timeout: int = Field(60, description="Request timeout in seconds")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens per response")
    temperature: float = Field(0.7, description="Sampling temperature")
    
    class Config:
        extra = "allow"


class OllamaConfig(ProviderConfig):
    """Ollama-specific configuration"""
    name: Literal["ollama"] = "ollama"
    server_url: str = "http://localhost:11434"
    model: str = "llama3.2:latest"


class OpenAIConfig(ProviderConfig):
    """OpenAI-specific configuration"""
    name: Literal["openai"] = "openai"
    model: str = "gpt-4"
    api_key: str


class AnthropicConfig(ProviderConfig):
    """Anthropic-specific configuration"""
    name: Literal["anthropic"] = "anthropic"
    model: str = "claude-3-opus-20240229"
    api_key: str


ProviderConfigUnion = Union[OllamaConfig, OpenAIConfig, AnthropicConfig, ProviderConfig]


# ============== Tool Configurations ==============

class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: str = "string"
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolConfig(BaseModel):
    """Tool configuration for MCP"""
    name: str
    description: str
    parameters: List[ToolParameter] = []
    handler: Optional[str] = Field(None, description="Python module path to handler")


# ============== Memory Configurations ==============

class MemoryConfig(BaseModel):
    """Conversation memory configuration"""
    type: Literal["conversation", "buffer", "vector", "none"] = "conversation"
    max_messages: int = Field(20, description="Maximum messages to retain")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to retain")


# ============== Output Configurations ==============

class OutputConfig(BaseModel):
    """Output configuration"""
    format: Literal["text", "markdown", "json"] = "markdown"
    streaming: bool = True
    include_metadata: bool = False


# ============== Agent Configuration ==============

class AgentConfig(BaseModel):
    """
    Agent configuration schema
    Each agent has its own YAML file documenting its use case
    """
    name: str = Field(..., description="Unique agent name")
    description: str = Field(..., description="Short description")
    use_case: str = Field(..., description="Detailed use case documentation")
    version: str = Field("1.0.0", description="Agent version")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    # Provider configuration
    provider: ProviderConfigUnion = Field(..., discriminator="name")
    
    # Capabilities
    capabilities: List[CapabilityType] = []
    custom_capabilities: List[str] = []
    
    # Tools
    tools: List[Union[str, ToolConfig]] = []
    
    # Memory
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    
    # Output
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # System prompt
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    
    class Config:
        extra = "allow"


# ============== A2A Server Configuration ==============

class A2AServerConfig(BaseModel):
    """
    A2A (Agent-to-Agent) Server configuration
    Facilitates communication between agents
    """
    name: str = Field(..., description="Server name")
    description: str = Field(..., description="Server description")
    use_case: str = Field(..., description="Detailed use case")
    version: str = "1.0.0"
    
    server: Dict[str, Any] = Field(default_factory=lambda: {
        "host": "0.0.0.0",
        "port": 8000,
        "protocol": "http"
    })
    
    # Registered agents
    agents: List[str] = []
    
    # Features
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "discovery": True,
        "routing": True,
        "load_balancing": True,
        "authentication": False
    })
    
    # Security
    auth: Optional[Dict[str, Any]] = None


# ============== MCP Server Configuration ==============

class MCPServerConfig(BaseModel):
    """
    MCP (Model Context Protocol) Server configuration
    Exposes tools and resources to agents
    """
    name: str = Field(..., description="Server name")
    description: str = Field(..., description="Server description")
    use_case: str = Field(..., description="Detailed use case")
    version: str = "1.0.0"
    
    # Transport
    transport: Literal["stdio", "sse", "websocket"] = "stdio"
    
    # Server settings
    server: Dict[str, Any] = Field(default_factory=dict)
    
    # Available tools
    tools: List[ToolConfig] = []
    
    # Available resources
    resources: List[Dict[str, Any]] = []


# ============== Framework Configuration ==============

class FrameworkConfig(BaseModel):
    """Main framework configuration"""
    name: str = "Hermes AI Framework"
    version: str = "1.0.0"
    
    # Global settings
    log_level: str = "INFO"
    config_dir: str = "./configs"
    
    # Auto-discovery
    auto_discover: bool = True
    
    # Health check
    health_check_interval: int = 30
