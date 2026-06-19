"""
Hermes AI Framework - Logging Module
Comprehensive logging for all framework components
"""
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import json


class HermesLogger:
    """Custom logger for Hermes AI Framework"""
    
    def __init__(self, name: str = "hermes", log_dir: str = "./logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler for all logs
        log_file = self.log_dir / f"hermes_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # Structured JSON log for events
        self.event_log_file = self.log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # Component loggers
        self.agents: Dict[str, logging.Logger] = {}
        self.servers: Dict[str, logging.Logger] = {}
    
    def get_agent_logger(self, agent_name: str) -> logging.Logger:
        """Get a logger for an agent"""
        if agent_name not in self.agents:
            logger = logging.getLogger(f"hermes.agent.{agent_name}")
            logger.setLevel(logging.DEBUG)
            
            # Agent-specific file
            agent_file = self.log_dir / f"agent_{agent_name}.log"
            handler = logging.FileHandler(agent_file)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            self.agents[agent_name] = logger
        
        return self.agents[agent_name]
    
    def get_server_logger(self, server_name: str) -> logging.Logger:
        """Get a logger for a server"""
        if server_name not in self.servers:
            logger = logging.getLogger(f"hermes.server.{server_name}")
            logger.setLevel(logging.DEBUG)
            
            # Server-specific file
            server_file = self.log_dir / f"server_{server_name}.log"
            handler = logging.FileHandler(server_file)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            self.servers[server_name] = logger
        
        return self.servers[server_name]
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a structured event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        
        with open(self.event_log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def log_agent_chat(self, agent_name: str, user_message: str, 
                       agent_response: str, metadata: Optional[Dict] = None) -> None:
        """Log agent chat interaction"""
        logger = self.get_agent_logger(agent_name)
        
        logger.info("=" * 60)
        logger.info(f"USER: {user_message}")
        logger.info(f"AGENT: {agent_response[:500]}{'...' if len(agent_response) > 500 else ''}")
        
        if metadata:
            logger.info(f"METADATA: {json.dumps(metadata)}")
        
        # Also log as event
        self.log_event("agent_chat", {
            "agent": agent_name,
            "user_message": user_message[:200],
            "response_length": len(agent_response),
            "metadata": metadata
        })
    
    def log_a2a_call(self, server_name: str, source: str, target: str, 
                     action: str, details: Optional[Dict] = None) -> None:
        """Log A2A server call"""
        logger = self.get_server_logger(server_name)
        
        msg = f"A2A CALL | {action} | Source: {source} | Target: {target}"
        if details:
            msg += f" | Details: {json.dumps(details)}"
        
        logger.info(msg)
        self.logger.info(f"[{server_name}] {msg}")
        
        # Log as event
        self.log_event("a2a_call", {
            "server": server_name,
            "action": action,
            "source": source,
            "target": target,
            "details": details
        })
    
    def log_mcp_call(self, server_name: str, tool_name: str, 
                     arguments: Dict, result: Any, duration_ms: float) -> None:
        """Log MCP tool call"""
        logger = self.get_server_logger(server_name)
        
        success = not (isinstance(result, dict) and 'error' in result)
        status = "SUCCESS" if success else "FAILED"
        
        msg = f"MCP TOOL | {tool_name} | Status: {status} | Duration: {duration_ms:.2f}ms"
        msg += f" | Args: {json.dumps(arguments)}"
        
        logger.info(msg)
        self.logger.info(f"[{server_name}] {msg}")
        
        # Log as event
        self.log_event("mcp_call", {
            "server": server_name,
            "tool": tool_name,
            "arguments": arguments,
            "success": success,
            "duration_ms": duration_ms
        })
    
    def log_agent_routing(self, from_agent: str, to_agent: str, 
                          reason: str, message_preview: str) -> None:
        """Log agent routing decision"""
        self.logger.info(f"AGENT ROUTING | {from_agent} -> {to_agent} | Reason: {reason}")
        
        self.log_event("agent_routing", {
            "from": from_agent,
            "to": to_agent,
            "reason": reason,
            "message_preview": message_preview[:100]
        })
    
    def log_system(self, message: str, level: str = "info") -> None:
        """Log system message"""
        getattr(self.logger, level)(message)
    
    def debug(self, msg: str) -> None:
        self.logger.debug(msg)
    
    def info(self, msg: str) -> None:
        self.logger.info(msg)
    
    def warning(self, msg: str) -> None:
        self.logger.warning(msg)
    
    def error(self, msg: str) -> None:
        self.logger.error(msg)
    
    def critical(self, msg: str) -> None:
        self.logger.critical(msg)


# Global logger instance
_hermes_logger: Optional[HermesLogger] = None


def get_logger(log_dir: str = "./logs") -> HermesLogger:
    """Get or create the global logger"""
    global _hermes_logger
    if _hermes_logger is None:
        _hermes_logger = HermesLogger(log_dir=log_dir)
    return _hermes_logger
