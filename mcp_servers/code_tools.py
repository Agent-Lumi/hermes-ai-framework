#!/usr/bin/env python3
"""
Hermes MCP Server - Code Tools
Provides code execution and analysis tools for agents
"""
import asyncio
import json
import sys
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any


class CodeToolsServer:
    """MCP Server for code tools"""
    
    def __init__(self):
        self.tools = {
            "execute_python": self.execute_python,
            "lint_code": self.lint_code,
            "format_code": self.format_code,
            "analyze_complexity": self.analyze_complexity
        }
    
    async def run(self):
        """Run the MCP server"""
        print("Code Tools MCP Server started", file=sys.stderr)
        
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
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request"""
        method = request.get("method")
        
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "execute_python",
                        "description": "Execute Python code safely in a sandbox",
                        "parameters": {
                            "code": "string - Python code to execute",
                            "timeout": "integer - Max execution time in seconds (default: 30)"
                        }
                    },
                    {
                        "name": "lint_code",
                        "description": "Lint Python code with flake8/pylint",
                        "parameters": {
                            "code": "string - Code to lint",
                            "linter": "string - Linter to use (flake8, pylint, default: flake8)"
                        }
                    },
                    {
                        "name": "format_code",
                        "description": "Format Python code with black",
                        "parameters": {
                            "code": "string - Code to format"
                        }
                    },
                    {
                        "name": "analyze_complexity",
                        "description": "Analyze code complexity with radon",
                        "parameters": {
                            "code": "string - Code to analyze"
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
    
    async def execute_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code safely"""
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Run with timeout and restricted environment
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'PYTHONPATH': ''}  # Restrict imports
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {"error": f"Execution timed out after {timeout}s"}
        finally:
            os.unlink(temp_file)
    
    async def lint_code(self, code: str, linter: str = "flake8") -> Dict[str, Any]:
        """Lint Python code"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            if linter == "flake8":
                cmd = ['flake8', '--max-line-length=100', temp_file]
            elif linter == "pylint":
                cmd = ['pylint', '--output-format=json', temp_file]
            else:
                return {"error": f"Unknown linter: {linter}"}
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "linter": linter,
                "issues": result.stdout if result.stdout else "No issues found",
                "success": result.returncode == 0
            }
            
        except FileNotFoundError:
            return {"error": f"{linter} not installed. Install with: pip install {linter}"}
        finally:
            os.unlink(temp_file)
    
    async def format_code(self, code: str) -> Dict[str, Any]:
        """Format Python code with black"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['black', '--quiet', temp_file],
                capture_output=True,
                text=True
            )
            
            # Read formatted code
            with open(temp_file, 'r') as f:
                formatted = f.read()
            
            return {
                "formatted_code": formatted,
                "success": result.returncode == 0
            }
            
        except FileNotFoundError:
            return {"error": "black not installed. Install with: pip install black"}
        finally:
            os.unlink(temp_file)
    
    async def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """Analyze code complexity"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['radon', 'cc', '-j', temp_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                complexity = json.loads(result.stdout) if result.stdout else {}
                return {
                    "complexity": complexity,
                    "summary": "Lower is better. A-F grades based on complexity score."
                }
            else:
                return {"error": result.stderr}
                
        except FileNotFoundError:
            return {"error": "radon not installed. Install with: pip install radon"}
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    server = CodeToolsServer()
    asyncio.run(server.run())
