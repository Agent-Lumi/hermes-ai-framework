"""
Hermes AI Framework - Provider Implementations
"""
import asyncio
import aiohttp
from typing import AsyncGenerator, Dict, Any, Optional, List
from abc import ABC, abstractmethod

from .config_models import ProviderConfig, OllamaConfig, OpenAIConfig


class BaseProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send chat messages and return response"""
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Send chat messages and yield response chunks"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        pass


class OllamaProvider(BaseProvider):
    """Ollama provider implementation"""
    
    def __init__(self, config: OllamaConfig):
        super().__init__(config)
        self.config: OllamaConfig = config
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send chat messages to Ollama"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.config.temperature)
                }
            }
            
            async with session.post(
                f"{self.config.server_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=kwargs.get('timeout', self.config.timeout))
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('message', {}).get('content', '')
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama error {response.status}: {error_text}")
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat messages from Ollama"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": kwargs.get('temperature', self.config.temperature)
                }
            }
            
            async with session.post(
                f"{self.config.server_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=kwargs.get('timeout', self.config.timeout))
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                import json
                                data = json.loads(line)
                                if 'message' in data:
                                    yield data['message'].get('content', '')
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama error {response.status}: {error_text}")
    
    async def health_check(self) -> bool:
        """Check if Ollama is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.server_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models from Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.server_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [m.get('name', m.get('model', 'unknown')) 
                                for m in data.get('models', [])]
                    return []
        except Exception as e:
            print(f"Error listing models: {e}")
            return []


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, config: OpenAIConfig):
        super().__init__(config)
        self.config: OpenAIConfig = config
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=config.api_key)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send chat messages to OpenAI"""
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=kwargs.get('temperature', self.config.temperature),
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens)
        )
        return response.choices[0].message.content or ""
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat messages from OpenAI"""
        stream = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=kwargs.get('temperature', self.config.temperature),
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            await self.client.models.list()
            return True
        except:
            return False


class ProviderFactory:
    """Factory for creating provider instances"""
    
    @staticmethod
    def create(config: ProviderConfig) -> BaseProvider:
        """Create provider instance based on config"""
        if config.name == "ollama":
            return OllamaProvider(config)
        elif config.name == "openai":
            return OpenAIProvider(config)
        else:
            raise ValueError(f"Unknown provider: {config.name}")
