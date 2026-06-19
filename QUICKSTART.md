# Hermes AI Framework - Quick Start Guide

## Prerequisites

```bash
# Clone the repository
git clone https://github.com/Agent-Lumi/hermes-ai-framework.git
cd hermes-ai-framework

# Install dependencies
pip install -r requirements.txt

# Install additional MCP server dependencies
pip install aiohttp beautifulsoup4  # For web_tools
pip install flake8 black radon       # For code_tools
```

## Step 1: Configure Ollama (Required)

The framework expects Ollama at `http://192.168.99.113:11434`

**Option A - Local Ollama:**
```bash
# Edit configs/providers/ollama.yaml
nano configs/providers/ollama.yaml

# Change server_url to your Ollama instance:
# server_url: http://localhost:11434
```

**Option B - Pull the model:**
```bash
# Ensure kimi-k2.5:cloud is available
ollama pull kimi-k2.5:cloud

# Or use any available model and update configs
ollama list
```

## Step 2: Start the A2A Server (Hub)

Terminal 1:
```bash
python hermes_cli.py server start hermes_hub
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

## Step 3: Start MCP Servers (Optional but recommended)

Terminal 2 - Code Tools:
```bash
python run_mcp_server.py code_tools
```

Terminal 3 - Web Tools:
```bash
python run_mcp_server.py web_tools
```

Terminal 4 - File Tools:
```bash
python run_mcp_server.py file_tools
```

## Step 4: Test the Framework

### Option A - Interactive Chat Interface

Terminal 5:
```bash
python chat_interface.py
```

Menu will appear:
```
1. List agents        → See available agents
2. Chat with agent    → Select and chat
3. Exit
```

**Try chatting:**
```
Select: 2
Agent: general_assistant

You: Hello, what can you do?
```

### Option B - CLI Commands

```bash
# List all agents
python hermes_cli.py agent list

# Chat with specific agent
python hermes_cli.py agent chat general_assistant

# Check agent info
python hermes_cli.py agent info code_specialist

# Clear agent memory
python hermes_cli.py agent clear general_assistant
```

### Option C - Direct Python

```python
import asyncio
from core.config_manager import ConfigManager
from core.agent import AgentManager

async def test():
    # Load configs
    config = ConfigManager("./configs")
    config.load_all()
    
    # Create agent
    manager = AgentManager()
    agent = manager.create_agent(config.get_agent("general_assistant"))
    
    # Start and chat
    await agent.start()
    response = await agent.chat("Hello, what is your purpose?")
    print(response)
    await agent.stop()

asyncio.run(test())
```

## Step 5: Test MCP Tools

### Test Code Execution
```bash
# In a new terminal
python run_mcp_server.py code_tools

# Then in another terminal, test with:
echo '{"method": "tools/invoke", "params": {"name": "execute_python", "arguments": {"code": "print(2+2)"}}}' | python mcp_servers/code_tools.py
```

### Test Web Scraping
```bash
python run_mcp_server.py web_tools

# The web_tools server is now ready for agents to use
```

### Test File Operations
```bash
python run_mcp_server.py file_tools

# Agents can now read/write files in /tmp and current directory
```

## Step 6: Check Logs

```bash
# View agent conversation logs
tail -f logs/agent_general_assistant.log

# View A2A server logs
tail -f logs/server_hermes_hub.log

# View MCP calls (JSON events)
tail -f logs/events_*.jsonl | jq .

# View all logs
tail -f logs/*.log
```

## Step 7: Test Specialized Agents

```bash
# Code Specialist - Ask coding questions
python chat_interface.py
# Select: code_specialist
# Ask: "Write a Python function to calculate fibonacci"

# Research Specialist - Deep research
# Select: research_specialist
# Ask: "What are the latest Python 3.12 features?"

# Creative Specialist - Writing help
# Select: creative_specialist
# Ask: "Write a poem about artificial intelligence"
```

## Step 8: Test A2A Communication

```bash
# In Python:
import requests

# Register an agent
requests.post("http://localhost:8000/register", json={
    "name": "test_agent",
    "endpoint": "http://localhost:9000",
    "capabilities": ["test"]
})

# List registered agents
curl http://localhost:8000/agents

# Discover by capability
curl "http://localhost:8000/discover?capability=code_generation"
```

## Troubleshooting

### "Provider not initialized"
```bash
# Check Ollama is running
curl http://192.168.99.113:11434/api/tags

# If not, update configs/providers/ollama.yaml
```

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Connection refused" on A2A server
```bash
# Check if server is running
python hermes_cli.py server list

# Or restart
python hermes_cli.py server start hermes_hub
```

### "Path not allowed" in file tools
```bash
# File tools only allow /tmp and current directory
# Use absolute paths or ensure files are in allowed directories
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│          User Interface                 │
│     (chat_interface.py or CLI)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Agent Manager                  │
│  (general_assistant, code_specialist) │
└─────────────────┬─────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌────▼────┐
│ A2A   │   │ Ollama  │   │ MCP     │
│ Server│   │ Provider│   │ Servers │
│ :8000 │   │ :11434  │   │ (stdio) │
└───────┘   └─────────┘   └─────────┘
```

## Quick Reference

| Component | Start Command | Port |
|-----------|--------------|------|
| A2A Server | `python hermes_cli.py server start hermes_hub` | 8000 |
| Code MCP | `python run_mcp_server.py code_tools` | stdio |
| Web MCP | `python run_mcp_server.py web_tools` | stdio |
| File MCP | `python run_mcp_server.py file_tools` | stdio |
| Chat UI | `python chat_interface.py` | - |

## Stopping Everything

```bash
# Stop A2A server
python hermes_cli.py server stop hermes_hub

# Or Ctrl+C in each terminal
# Logs are preserved in logs/ directory
```

## Next Steps

1. **Customize agents**: Edit configs/agents/*.yaml
2. **Add new MCP tools**: Edit mcp_servers/*.py
3. **Create new agents**: Copy configs/agents/general_assistant.yaml
4. **Connect external agents**: Use A2A API at localhost:8000
