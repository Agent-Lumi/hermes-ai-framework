#!/usr/bin/env python3
"""
Hermes MCP Server - File Tools
Provides file system operations for agents
"""
import asyncio
import json
import sys
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import hashlib


class FileToolsServer:
    """MCP Server for file operations"""
    
    def __init__(self, allowed_paths: List[str] = None):
        self.allowed_paths = allowed_paths or [os.getcwd()]
        self.tools = {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "list_directory": self.list_directory,
            "search_files": self.search_files,
            "get_file_info": self.get_file_info,
            "create_directory": self.create_directory,
            "delete_file": self.delete_file
        }
    
    def is_allowed(self, path: str) -> bool:
        """Check if path is in allowed directories"""
        path = Path(path).resolve()
        for allowed in self.allowed_paths:
            allowed_path = Path(allowed).resolve()
            try:
                path.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        return False
    
    async def run(self):
        """Run the MCP server"""
        print("File Tools MCP Server started", file=sys.stderr)
        
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
                        "name": "read_file",
                        "description": "Read contents of a file",
                        "parameters": {
                            "path": "string - File path",
                            "limit": "integer - Max lines to read (default: 500)"
                        }
                    },
                    {
                        "name": "write_file",
                        "description": "Write content to a file",
                        "parameters": {
                            "path": "string - File path",
                            "content": "string - Content to write"
                        }
                    },
                    {
                        "name": "list_directory",
                        "description": "List files in a directory",
                        "parameters": {
                            "path": "string - Directory path",
                            "recursive": "boolean - List recursively (default: false)"
                        }
                    },
                    {
                        "name": "search_files",
                        "description": "Search for files by pattern",
                        "parameters": {
                            "pattern": "string - Search pattern (e.g., *.py)",
                            "path": "string - Directory to search in"
                        }
                    },
                    {
                        "name": "get_file_info",
                        "description": "Get file metadata",
                        "parameters": {
                            "path": "string - File path"
                        }
                    },
                    {
                        "name": "create_directory",
                        "description": "Create a directory",
                        "parameters": {
                            "path": "string - Directory path"
                        }
                    },
                    {
                        "name": "delete_file",
                        "description": "Delete a file or directory",
                        "parameters": {
                            "path": "string - File or directory path",
                            "recursive": "boolean - Delete recursively if directory"
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
    
    async def read_file(self, path: str, limit: int = 500) -> Dict[str, Any]:
        """Read file contents"""
        if not self.is_allowed(path):
            return {"error": "Path not allowed"}
        
        try:
            with open(path, 'r') as f:
                lines = f.readlines()[:limit]
                content = ''.join(lines)
            
            return {
                "path": path,
                "content": content,
                "lines": len(lines),
                "truncated": len(lines) == limit
            }
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        if not self.is_allowed(path):
            return {"error": "Path not allowed"}
        
        try:
            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                f.write(content)
            
            return {
                "path": path,
                "bytes_written": len(content),
                "success": True
            }
        except Exception as e:
            return {"error": f"Failed to write file: {e}"}
    
    async def list_directory(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """List directory contents"""
        if not self.is_allowed(path):
            return {"error": "Path not allowed"}
        
        try:
            entries = []
            base_path = Path(path)
            
            if recursive:
                for item in base_path.rglob('*'):
                    entries.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None
                    })
            else:
                for item in base_path.iterdir():
                    entries.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None
                    })
            
            return {
                "path": path,
                "entries": entries,
                "count": len(entries)
            }
        except Exception as e:
            return {"error": f"Failed to list directory: {e}"}
    
    async def search_files(self, pattern: str, path: str) -> Dict[str, Any]:
        """Search for files"""
        if not self.is_allowed(path):
            return {"error": "Path not allowed"}
        
        try:
            base_path = Path(path)
            matches = list(base_path.rglob(pattern))
            
            return {
                "pattern": pattern,
                "path": path,
                "matches": [str(m) for m in matches],
                "count": len(matches)
            }
        except Exception as e:
            return {"error": f"Failed to search: {e}"}
    
    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file metadata"""
        if not self.is_allowed(path):
            return {"error": "Path not allowed"}
        
        try:
            p = Path(path)
            stat = p.stat()
            
            info = {
                "path": path,
                "exists": p.exists(),
                "is_file": p.is_file(),
                "is_dir": p.is_dir(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime
            }
            
            if p.is_file():
                # Calculate hash
                with open(path, 'rb') as f:
                    info["md5"] = hashlib.md5(f.read()).hexdigest()
            
            return info
        except Exception as e:
            return {"error": f"Failed to get file info: {e}"}
    
    async def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory"""
        if not self.is_allowed(path):
            return {"error": "Path not allowed"}
        
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return {
                "path": path,
                "created": True
            }
        except Exception as e:
            return {"error": f"Failed to create directory: {e}"}
    
    async def delete_file(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """Delete file or directory"""
        if not self.is_allowed(path):
            return {"error": "Path not allowed"}
        
        try:
            p = Path(path)
            
            if p.is_file():
                p.unlink()
                return {"path": path, "deleted": True, "type": "file"}
            elif p.is_dir():
                if recursive:
                    shutil.rmtree(path)
                else:
                    p.rmdir()
                return {"path": path, "deleted": True, "type": "directory"}
            else:
                return {"error": "Path not found"}
                
        except Exception as e:
            return {"error": f"Failed to delete: {e}"}


if __name__ == "__main__":
    # Allow access to current working directory and /tmp
    allowed = [os.getcwd(), '/tmp']
    server = FileToolsServer(allowed_paths=allowed)
    asyncio.run(server.run())
