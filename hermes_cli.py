"""
Hermes AI Framework - CLI
Command line interface for managing the framework
"""
import click
import asyncio
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager
from core.agent import AgentManager
from core.config_models import AgentConfig

console = Console()

# Global state
config_manager: Optional[ConfigManager] = None
agent_manager: Optional[AgentManager] = None


def get_config_manager():
    """Get or create config manager"""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager("./configs")
        config_manager.load_all()
    return config_manager


def get_agent_manager():
    """Get or create agent manager"""
    global agent_manager
    if agent_manager is None:
        agent_manager = AgentManager()
        # Load agents from config
        cm = get_config_manager()
        for name, config in cm.agents.items():
            agent_manager.create_agent(config)
    return agent_manager


@click.group()
@click.option('--config-dir', default='./configs', help='Configuration directory')
@click.pass_context
def cli(ctx, config_dir):
    """Hermes AI Framework CLI
    
    Manage AI agents, A2A servers, and MCP servers
    """
    ctx.ensure_object(dict)
    ctx.obj['config_dir'] = config_dir


# ============== Agent Commands ==============

@cli.group()
def agent():
    """Manage AI agents"""
    pass


@agent.command('list')
def agent_list():
    """List all configured agents"""
    cm = get_config_manager()
    
    if not cm.agents:
        console.print("[yellow]No agents configured[/yellow]")
        return
    
    table = Table(title="Configured Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Provider", style="blue")
    table.add_column("Model", style="magenta")
    table.add_column("Capabilities", style="yellow")
    
    for name, config in cm.agents.items():
        caps = ", ".join(str(c) for c in config.capabilities[:3])
        if len(config.capabilities) > 3:
            caps += "..."
        
        table.add_row(
            config.name,
            config.description[:50] + "..." if len(config.description) > 50 else config.description,
            config.provider.name,
            config.provider.model,
            caps or "none"
        )
    
    console.print(table)


@agent.command('show')
@click.argument('name')
def agent_show(name):
    """Show agent details"""
    cm = get_config_manager()
    config = cm.get_agent(name)
    
    if not config:
        console.print(f"[red]Agent '{name}' not found[/red]")
        return
    
    # Display agent info
    info = Text()
    info.append(f"Name: ", style="bold")
    info.append(f"{config.name}\n")
    info.append(f"Description: ", style="bold")
    info.append(f"{config.description}\n")
    info.append(f"Use Case:\n", style="bold")
    info.append(f"{config.use_case}\n\n")
    info.append(f"Provider: ", style="bold")
    info.append(f"{config.provider.name}\n")
    info.append(f"Model: ", style="bold")
    info.append(f"{config.provider.model}\n")
    info.append(f"Capabilities: ", style="bold")
    info.append(f"{', '.join(str(c) for c in config.capabilities)}\n")
    info.append(f"Memory: ", style="bold")
    info.append(f"{config.memory.type} (max {config.memory.max_messages} messages)\n")
    info.append(f"Output: ", style="bold")
    info.append(f"{config.output.format} (streaming: {config.output.streaming})")
    
    console.print(Panel(info, title=f"Agent: {config.name}", border_style="cyan"))


@agent.command('start')
@click.argument('name')
def agent_start(name):
    """Start an agent"""
    async def _start():
        am = get_agent_manager()
        agent = am.get_agent(name)
        
        if not agent:
            # Try to load from config
            cm = get_config_manager()
            config = cm.get_agent(name)
            if config:
                agent = am.create_agent(config)
            else:
                console.print(f"[red]Agent '{name}' not found[/red]")
                return
        
        try:
            await agent.start()
            console.print(f"[green]Agent '{name}' started successfully[/green]")
        except Exception as e:
            console.print(f"[red]Failed to start agent: {e}[/red]")
    
    asyncio.run(_start())


@agent.command('chat')
@click.argument('name')
@click.option('--message', '-m', help='Message to send')
def agent_chat(name, message):
    """Chat with an agent"""
    async def _chat():
        am = get_agent_manager()
        agent = am.get_agent(name)
        
        if not agent:
            console.print(f"[red]Agent '{name}' not found. Start it first with: hermes-cli agent start {name}[/red]")
            return
        
        if message:
            # Single message mode
            with console.status(f"[cyan]Agent '{name}' is thinking..."):
                response = await agent.chat(message)
            console.print(f"[green]{name}:[/green] {response}")
        else:
            # Interactive mode
            console.print(f"[cyan]Chatting with {name}. Type 'quit' to exit.[/cyan]\n")
            
            while True:
                user_input = console.input("[bold blue]You: [/bold blue]")
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                with console.status(f"[cyan]{name} is thinking..."):
                    response = await agent.chat(user_input)
                
                console.print(f"[green]{name}:[/green] {response}\n")
    
    asyncio.run(_chat())


@agent.command('create')
@click.argument('name')
@click.option('--provider', default='ollama', help='Provider name')
@click.option('--model', default='llama3.2:latest', help='Model name')
@click.option('--description', '-d', default='', help='Agent description')
def agent_create(name, provider, model, description):
    """Create a new agent configuration"""
    import yaml
    
    config = {
        "name": name,
        "description": description or f"Agent {name}",
        "use_case": f"Agent created via CLI\n\nThis agent uses {provider} with model {model}",
        "provider": {
            "name": provider,
            "model": model
        },
        "capabilities": [],
        "memory": {
            "type": "conversation",
            "max_messages": 20
        },
        "output": {
            "format": "markdown",
            "streaming": True
        }
    }
    
    config_path = Path("./configs/agents") / f"{name}.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"[green]Created agent config: {config_path}[/green]")
    console.print(f"[cyan]Edit this file to customize your agent![/cyan]")


# ============== Server Commands ==============

@cli.group()
def server():
    """Manage A2A and MCP servers"""
    pass


@server.command('list')
def server_list():
    """List all servers"""
    cm = get_config_manager()
    
    # A2A Servers
    if cm.a2a_servers:
        console.print("\n[bold cyan]A2A Servers:[/bold cyan]")
        table = Table()
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Port", style="blue")
        
        for name, config in cm.a2a_servers.items():
            table.add_row(
                config.name,
                config.description[:40] + "..." if len(config.description) > 40 else config.description,
                str(config.server.get('port', 'N/A'))
            )
        console.print(table)
    
    # MCP Servers
    if cm.mcp_servers:
        console.print("\n[bold cyan]MCP Servers:[/bold cyan]")
        table = Table()
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Transport", style="blue")
        table.add_column("Tools", style="magenta")
        
        for name, config in cm.mcp_servers.items():
            table.add_row(
                config.name,
                config.description[:40] + "..." if len(config.description) > 40 else config.description,
                config.transport,
                str(len(config.tools))
            )
        console.print(table)


@server.command('start')
@click.argument('name')
def server_start(name):
    """Start an A2A or MCP server"""
    async def _start():
        cm = get_config_manager()
        
        # Check if it's an A2A server
        if name in cm.a2a_servers:
            from core.a2a_server import A2AServer
            config = cm.a2a_servers[name]
            server = A2AServer(config)
            
            console.print(f"[cyan]Starting A2A server '{name}'...[/cyan]")
            await server.start()
            
            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await server.stop()
        
        # Check if it's an MCP server
        elif name in cm.mcp_servers:
            console.print(f"[yellow]MCP servers should be started with: python run_mcp_server.py {name}[/yellow]")
            return
        
        else:
            console.print(f"[red]Server '{name}' not found.[/red]")
            console.print("Available servers:")
            for s in list(cm.a2a_servers.keys()) + list(cm.mcp_servers.keys()):
                console.print(f"  - {s}")
    
    try:
        asyncio.run(_start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")


@server.command('stop')
@click.argument('name')
def server_stop(name):
    """Stop a server (placeholder - use Ctrl+C to stop)"""
    console.print(f"[yellow]To stop a server, press Ctrl+C in its terminal[/yellow]")
    console.print(f"[dim]Server '{name}' state is managed by its process[/dim]")


# ============== Framework Commands ==============

@cli.command('init')
def init_framework():
    """Initialize the framework with example configurations"""
    cm = get_config_manager()
    cm.create_example_configs()
    console.print("[green]Framework initialized with example configurations![/green]")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("  1. Review configs in ./configs/")
    console.print("  2. Edit configurations to match your setup")
    console.print("  3. Start an agent: hermes-cli agent start code_assistant")


@cli.command('status')
def framework_status():
    """Show framework status"""
    cm = get_config_manager()
    
    console.print(Panel(
        f"[bold]Hermes AI Framework[/bold]\n\n"
        f"Agents: {len(cm.agents)}\n"
        f"A2A Servers: {len(cm.a2a_servers)}\n"
        f"MCP Servers: {len(cm.mcp_servers)}\n"
        f"Providers: {len(cm.providers)}",
        title="Status",
        border_style="cyan"
    ))


@cli.command('validate')
def validate_configs():
    """Validate all configurations"""
    cm = get_config_manager()
    if cm.validate_all():
        console.print("[green]All configurations are valid![/green]")
    else:
        console.print("[red]Some configurations have errors[/red]")
        raise click.Abort()


if __name__ == '__main__':
    cli()
