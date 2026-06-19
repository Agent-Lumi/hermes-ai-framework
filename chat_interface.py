"""
Hermes AI Framework - Chat Interface
Interactive chat with agents
"""
import asyncio
import sys
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.prompt import Prompt

from core.config_manager import ConfigManager
from core.agent import AgentManager, Agent

console = Console()


class ChatInterface:
    """Interactive chat interface for agents"""
    
    def __init__(self, config_dir: str = "./configs"):
        self.config_manager = ConfigManager(config_dir)
        self.agent_manager = AgentManager()
        self.current_agent: Optional[Agent] = None
        self.history: List[dict] = []
    
    def load_agents(self) -> None:
        """Load all agents from configuration"""
        self.config_manager.load_all()
        
        for name, config in self.config_manager.agents.items():
            try:
                self.agent_manager.create_agent(config)
                console.print(f"[green]✓[/green] Loaded agent: {name}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to load {name}: {e}")
    
    def list_agents(self) -> None:
        """Display list of available agents"""
        agents = self.agent_manager.list_agents()
        
        if not agents:
            console.print("[yellow]No agents available[/yellow]")
            return
        
        table_text = Text()
        table_text.append("Available Agents:\n\n", style="bold cyan")
        
        for i, name in enumerate(agents, 1):
            agent = self.agent_manager.get_agent(name)
            if agent:
                info = agent.get_info()
                table_text.append(f"{i}. ", style="dim")
                table_text.append(f"{name}\n", style="green")
                table_text.append(f"   {info['description']}\n", style="dim")
                table_text.append(f"   Provider: {info['provider']}/{info['model']}\n\n", style="blue")
        
        console.print(Panel(table_text, border_style="cyan"))
    
    async def chat_with_agent(self, agent_name: str) -> None:
        """Start interactive chat with an agent"""
        agent = self.agent_manager.get_agent(agent_name)
        
        if not agent:
            # Try to load
            config = self.config_manager.get_agent(agent_name)
            if config:
                agent = self.agent_manager.create_agent(config)
            else:
                console.print(f"[red]Agent '{agent_name}' not found[/red]")
                return
        
        # Start the agent
        try:
            await agent.start()
        except Exception as e:
            console.print(f"[red]Failed to start agent: {e}[/red]")
            return
        
        self.current_agent = agent
        
        # Display chat header
        console.print(Panel(
            f"[bold cyan]Chatting with {agent.config.name}[/bold cyan]\n"
            f"[dim]{agent.config.description}[/dim]\n\n"
            f"Type [bold]'/help'[/bold] for commands, [bold]'/exit'[/bold] to quit",
            border_style="cyan"
        ))
        
        # Chat loop
        while True:
            try:
                user_input = console.input("\n[bold blue]You: [/bold blue]").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    if await self.handle_command(user_input):
                        break
                    continue
                
                # Show thinking indicator
                with console.status(f"[cyan]{agent.config.name} is thinking..."):
                    response = await agent.chat(user_input)
                
                # Display response
                console.print(f"[green]{agent.config.name}:[/green] {response}\n")
                
                # Add to history
                self.history.append({
                    "agent": agent_name,
                    "user": user_input,
                    "assistant": response
                })
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Use '/exit' to quit.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
        # Stop the agent
        await agent.stop()
        self.current_agent = None
    
    async def chat_streaming(self, agent_name: str, message: str) -> None:
        """Chat with streaming response"""
        agent = self.agent_manager.get_agent(agent_name)
        
        if not agent:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
            return
        
        # Display user message
        console.print(f"\n[bold blue]You:[/bold blue] {message}")
        console.print(f"\n[green]{agent.config.name}:[/green] ", end="")
        
        # Stream response
        full_response = []
        try:
            async for chunk in agent.chat_stream(message):
                console.print(chunk, end="")
                full_response.append(chunk)
            console.print()  # New line after response
            
            # Add to history
            self.history.append({
                "agent": agent_name,
                "user": message,
                "assistant": "".join(full_response)
            })
            
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
    
    async def handle_command(self, command: str) -> bool:
        """Handle special commands, returns True if should exit"""
        cmd = command.lower()
        
        if cmd == '/exit' or cmd == '/quit':
            console.print("[yellow]Ending chat...[/yellow]")
            return True
        
        elif cmd == '/help':
            help_text = """
[bold]Available Commands:[/bold]

/clear       - Clear conversation memory
/history     - Show conversation history
/info        - Show agent information
/switch <n>  - Switch to different agent
/stream <msg>- Send message with streaming
/help        - Show this help message
/exit        - End chat session
            """
            console.print(Panel(help_text, title="Help", border_style="cyan"))
        
        elif cmd == '/clear':
            if self.current_agent:
                self.current_agent.clear_memory()
                console.print("[green]Memory cleared[/green]")
        
        elif cmd == '/history':
            if self.current_agent:
                history = self.current_agent.get_memory()
                if not history:
                    console.print("[dim]No history yet[/dim]")
                else:
                    for msg in history:
                        role_color = "blue" if msg['role'] == 'user' else "green"
                        console.print(f"[{role_color}]{msg['role'].capitalize()}:[/{role_color}] {msg['content'][:100]}...")
        
        elif cmd == '/info':
            if self.current_agent:
                info = self.current_agent.get_info()
                info_text = "\n".join(f"[cyan]{k}:[/cyan] {v}" for k, v in info.items())
                console.print(Panel(info_text, title="Agent Info", border_style="cyan"))
        
        elif cmd.startswith('/switch '):
            new_agent = command.split(' ', 1)[1]
            console.print(f"[yellow]Switching to {new_agent}...[/yellow]")
            return True  # Signal to exit current chat
        
        elif cmd.startswith('/stream '):
            message = command.split(' ', 1)[1]
            if self.current_agent:
                await self.chat_streaming(self.current_agent.config.name, message)
        
        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
        
        return False
    
    async def run_interactive(self) -> None:
        """Run interactive mode"""
        console.print(Panel.fit(
            "[bold cyan]Hermes AI Framework - Chat Interface[/bold cyan]\n"
            "[dim]Interactive chat with AI agents[/dim]",
            border_style="cyan"
        ))
        
        # Load agents
        with console.status("[cyan]Loading agents..."):
            self.load_agents()
        
        # Main menu loop
        while True:
            console.print("\n" + "=" * 60)
            console.print("[bold]Main Menu[/bold]")
            console.print("1. List agents")
            console.print("2. Chat with agent")
            console.print("3. Exit")
            
            choice = console.input("\n[bold]Choice: [/bold]").strip()
            
            if choice == '1':
                self.list_agents()
            
            elif choice == '2':
                self.list_agents()
                agent_name = console.input("\n[bold]Enter agent name: [/bold]").strip()
                if agent_name:
                    await self.chat_with_agent(agent_name)
            
            elif choice == '3':
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            else:
                console.print("[red]Invalid choice[/red]")


async def main():
    """Main entry point for chat interface"""
    chat = ChatInterface()
    await chat.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
