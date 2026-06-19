# Hermes AI Framework
# A configurable framework for AI agents, A2A servers, and MCP servers

## Overview

Hermes AI Framework allows you to spin up and manage:
- **AI Agents** - Autonomous AI workers with specific capabilities
- **A2A Servers** - Agent-to-Agent communication servers
- **MCP Servers** - Model Context Protocol servers for tool integration

## Quick Start

**New?** See the [QUICKSTART.md](QUICKSTART.md) for step-by-step instructions.

```bash
# Install dependencies
pip install -r requirements.txt

# Start the framework
python -m hermes_framework

# Or use the CLI
hermes-cli agent start configs/agents/coder.yaml
```

## Configuration Structure

```
configs/
├── agents/           # Agent configurations
├── a2a_servers/      # A2A server configurations
├── mcp_servers/      # MCP server configurations
└── providers/        # Provider configurations (Ollama, OpenAI, etc.)
```

## Creating an Agent

1. Create a YAML config in `configs/agents/`:

```yaml
# configs/agents/my_agent.yaml
name: code_assistant
description: A coding assistant that helps with Python and SQL
use_case: |
  This agent assists with:
  - Writing Python code
  - SQL query optimization
  - Code review and debugging

provider:
  name: ollama
  model: llama3.2:latest
  server_url: http://192.168.99.113:11434

capabilities:
  - code_generation
  - code_review
  - sql_optimization

tools:
  - python_executor
  - sql_analyzer

memory:
  type: conversation
  max_messages: 20

output:
  format: markdown
  streaming: true
```

2. Start the agent:

```bash
hermes-cli agent start configs/agents/my_agent.yaml
```

## Creating an A2A Server

```yaml
# configs/a2a_servers/main.yaml
name: hermes_a2a_hub
description: Central A2A communication hub
use_case: |
  Facilitates agent-to-agent communication
  Routes messages between registered agents
  Provides discovery service

server:
  host: 0.0.0.0
  port: 8000
  protocol: http

agents:
  - code_assistant
  - data_analyst
  - web_researcher

features:
  discovery: true
  routing: true
  load_balancing: true
```

## Creating an MCP Server

```yaml
# configs/mcp_servers/tools.yaml
name: tool_registry
description: MCP server providing tool access to agents
use_case: |
  Exposes tools via MCP protocol:
  - Database queries
  - Web scraping
  - File operations

tools:
  - name: database_query
    description: Execute SQL queries
    parameters:
      connection_string: string
      query: string
    
  - name: web_scrape
    description: Scrape web content
    parameters:
      url: string
      selector: string

server:
  transport: stdio  # or sse
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Hermes Framework                      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Agents  │  │  A2A     │  │  MCP     │              │
│  │          │  │  Servers │  │  Servers │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │             │                      │
│       └─────────────┼─────────────┘                      │
│                     │                                    │
│              ┌──────┴──────┐                            │
│              │   Core      │                            │
│              │  Manager    │                            │
│              └──────┬──────┘                            │
│                     │                                    │
│              ┌──────┴──────┐                            │
│              │  Providers  │                            │
│              │  (Ollama,   │                            │
│              │   OpenAI)   │                            │
│              └─────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

## License

MIT
