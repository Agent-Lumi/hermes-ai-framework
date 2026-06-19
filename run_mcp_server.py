#!/usr/bin/env python3
"""
Hermes MCP Server Runner
Launches MCP servers with proper logging
"""
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import List

# MCP servers configuration
MCP_SERVERS = {
    "code_tools": {
        "script": "mcp_servers/code_tools.py",
        "description": "Code execution and analysis"
    },
    "web_tools": {
        "script": "mcp_servers/web_tools.py",
        "description": "Web scraping and search"
    },
    "file_tools": {
        "script": "mcp_servers/file_tools.py",
        "description": "File system operations"
    }
}


def run_mcp_server(name: str):
    """Run a single MCP server"""
    if name not in MCP_SERVERS:
        print(f"Unknown MCP server: {name}")
        print(f"Available: {', '.join(MCP_SERVERS.keys())}")
        return
    
    config = MCP_SERVERS[name]
    script_path = Path(config["script"])
    
    if not script_path.exists():
        print(f"Script not found: {script_path}")
        return
    
    print(f"Starting MCP server: {name}")
    print(f"Description: {config['description']}")
    print(f"Script: {script_path}")
    
    try:
        subprocess.run([sys.executable, str(script_path)])
    except KeyboardInterrupt:
        print(f"\nStopping MCP server: {name}")


def list_servers():
    """List available MCP servers"""
    print("Available MCP Servers:")
    print("-" * 50)
    for name, config in MCP_SERVERS.items():
        print(f"  {name:15} - {config['description']}")
        print(f"  {'':15}   ({config['script']})")
        print()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Hermes MCP servers")
    parser.add_argument("server", nargs="?", help="MCP server to run")
    parser.add_argument("--list", "-l", action="store_true", help="List available servers")
    
    args = parser.parse_args()
    
    if args.list:
        list_servers()
    elif args.server:
        run_mcp_server(args.server)
    else:
        parser.print_help()
        print("\n")
        list_servers()


if __name__ == "__main__":
    main()
