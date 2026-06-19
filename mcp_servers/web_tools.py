#!/usr/bin/env python3
"""
Hermes MCP Server - Web Tools
Provides web scraping, search, and HTTP tools for agents
"""
import asyncio
import json
import sys
from typing import Dict, Any, Optional
from urllib.parse import urlparse

try:
    import aiohttp
    from bs4 import BeautifulSoup
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class WebToolsServer:
    """MCP Server for web tools"""
    
    def __init__(self):
        self.tools = {
            "fetch_url": self.fetch_url,
            "extract_text": self.extract_text,
            "search_duckduckgo": self.search_duckduckgo,
            "check_link": self.check_link
        }
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if AIOHTTP_AVAILABLE and not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def run(self):
        """Run the MCP server"""
        print("Web Tools MCP Server started", file=sys.stderr)
        
        await self.init_session()
        
        try:
            while True:
                try:
                    line = input()
                    if not line:
                        continue
                    
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    print(json.dumps({"error": f"Invalid JSON: {e}"}), flush=True)
                except EOFError:
                    break
                except Exception as e:
                    print(json.dumps({"error": str(e)}), flush=True)
        finally:
            await self.close_session()
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request"""
        method = request.get("method")
        
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "fetch_url",
                        "description": "Fetch HTML content from a URL",
                        "parameters": {
                            "url": "string - URL to fetch",
                            "timeout": "integer - Request timeout in seconds (default: 30)"
                        }
                    },
                    {
                        "name": "extract_text",
                        "description": "Extract readable text from HTML",
                        "parameters": {
                            "html": "string - HTML content",
                            "max_length": "integer - Maximum text length (default: 5000)"
                        }
                    },
                    {
                        "name": "search_duckduckgo",
                        "description": "Search DuckDuckGo (limited results)",
                        "parameters": {
                            "query": "string - Search query",
                            "num_results": "integer - Number of results (default: 5)"
                        }
                    },
                    {
                        "name": "check_link",
                        "description": "Check if a URL is accessible",
                        "parameters": {
                            "url": "string - URL to check"
                        }
                    }
                ]
            }
        
        elif method == "tools/invoke":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name in self.tools:
                try:
                    result = await self.tools[tool_name](**arguments)
                    return {"result": result}
                except Exception as e:
                    return {"error": str(e)}
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        return {"error": f"Unknown method: {method}"}
    
    async def fetch_url(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """Fetch HTML from URL"""
        if not AIOHTTP_AVAILABLE:
            return {"error": "aiohttp not installed. Run: pip install aiohttp"}
        
        if not self.session:
            await self.init_session()
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                html = await response.text()
                return {
                    "url": str(response.url),
                    "status": response.status,
                    "content_type": response.headers.get('content-type', 'unknown'),
                    "html": html[:50000],  # Limit size
                    "size": len(html)
                }
        except Exception as e:
            return {"error": f"Failed to fetch {url}: {str(e)}"}
    
    async def extract_text(self, html: str, max_length: int = 5000) -> Dict[str, Any]:
        """Extract readable text from HTML"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n')
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate if needed
            truncated = len(text) > max_length
            text = text[:max_length]
            
            return {
                "text": text,
                "truncated": truncated,
                "original_length": len(html),
                "extracted_length": len(text)
            }
            
        except ImportError:
            return {"error": "beautifulsoup4 not installed. Run: pip install beautifulsoup4"}
    
    async def search_duckduckgo(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search DuckDuckGo"""
        if not AIOHTTP_AVAILABLE:
            return {"error": "aiohttp not installed"}
        
        # DuckDuckGo HTML version
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        
        try:
            async with self.session.get(search_url) as response:
                html = await response.text()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                results = []
                for result in soup.select('.result')[:num_results]:
                    title_elem = result.select_one('.result__a')
                    snippet_elem = result.select_one('.result__snippet')
                    
                    if title_elem:
                        results.append({
                            "title": title_elem.get_text(strip=True),
                            "url": title_elem.get('href', ''),
                            "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                        })
                
                return {
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
                
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    async def check_link(self, url: str) -> Dict[str, Any]:
        """Check if URL is accessible"""
        if not AIOHTTP_AVAILABLE:
            return {"error": "aiohttp not installed"}
        
        try:
            async with self.session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return {
                    "url": url,
                    "accessible": response.status < 400,
                    "status_code": response.status,
                    "final_url": str(response.url)
                }
        except Exception as e:
            return {
                "url": url,
                "accessible": False,
                "error": str(e)
            }


if __name__ == "__main__":
    server = WebToolsServer()
    asyncio.run(server.run())
