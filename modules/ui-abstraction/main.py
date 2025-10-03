"""
AI-SERVIS UI Abstraction Main Module
Coordinates all UI interfaces and provides unified management
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from ui_models import (
    UIManager, UIAdapterConfig, InterfaceType, MessageType,
    UIMessage, CommandMessage, ResponseMessage, StatusMessage, ErrorMessage
)
from voice_interface import VoiceInterface
from text_interface import TextInterface
from web_interface import WebInterface
from mobile_interface import MobileInterface

# Import MCP framework for orchestrator communication
from mcp_framework import MCPClient

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UIAbstractionManager:
    """Main UI abstraction manager"""
    
    def __init__(self):
        self.ui_manager = UIManager()
        self.orchestrator_client = None
        self.config = self._load_config()
        self.is_running = False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment or defaults"""
        return {
            "voice_interface": {
                "enabled": os.getenv("VOICE_INTERFACE_ENABLED", "true").lower() == "true",
                "host": os.getenv("VOICE_INTERFACE_HOST", "localhost"),
                "port": int(os.getenv("VOICE_INTERFACE_PORT", "8081")),
                "max_connections": int(os.getenv("VOICE_MAX_CONNECTIONS", "100")),
                "timeout": int(os.getenv("VOICE_TIMEOUT", "30"))
            },
            "text_interface": {
                "enabled": os.getenv("TEXT_INTERFACE_ENABLED", "true").lower() == "true",
                "host": os.getenv("TEXT_INTERFACE_HOST", "localhost"),
                "port": int(os.getenv("TEXT_INTERFACE_PORT", "8082")),
                "max_connections": int(os.getenv("TEXT_MAX_CONNECTIONS", "100")),
                "timeout": int(os.getenv("TEXT_TIMEOUT", "30")),
                "enable_cli": os.getenv("TEXT_ENABLE_CLI", "true").lower() == "true"
            },
            "web_interface": {
                "enabled": os.getenv("WEB_INTERFACE_ENABLED", "true").lower() == "true",
                "host": os.getenv("WEB_INTERFACE_HOST", "localhost"),
                "port": int(os.getenv("WEB_INTERFACE_PORT", "8083")),
                "max_connections": int(os.getenv("WEB_MAX_CONNECTIONS", "100")),
                "timeout": int(os.getenv("WEB_TIMEOUT", "30")),
                "ssl_enabled": os.getenv("WEB_SSL_ENABLED", "false").lower() == "true"
            },
            "mobile_interface": {
                "enabled": os.getenv("MOBILE_INTERFACE_ENABLED", "true").lower() == "true",
                "host": os.getenv("MOBILE_INTERFACE_HOST", "localhost"),
                "port": int(os.getenv("MOBILE_INTERFACE_PORT", "8084")),
                "max_connections": int(os.getenv("MOBILE_MAX_CONNECTIONS", "100")),
                "timeout": int(os.getenv("MOBILE_TIMEOUT", "30")),
                "authentication_required": os.getenv("MOBILE_AUTH_REQUIRED", "true").lower() == "true"
            },
            "orchestrator": {
                "host": os.getenv("ORCHESTRATOR_HOST", "localhost"),
                "port": int(os.getenv("ORCHESTRATOR_PORT", "8080")),
                "protocol": os.getenv("ORCHESTRATOR_PROTOCOL", "http")
            }
        }
    
    async def start(self) -> None:
        """Start all UI interfaces"""
        try:
            logger.info("Starting AI-SERVIS UI Abstraction Manager")
            
            # Connect to orchestrator
            await self._connect_to_orchestrator()
            
            # Initialize and register interfaces
            await self._initialize_interfaces()
            
            # Start all interfaces
            await self.ui_manager.start_all()
            
            self.is_running = True
            logger.info("UI Abstraction Manager started successfully")
            
            # Start background tasks
            asyncio.create_task(self._monitor_connections())
            asyncio.create_task(self._health_check())
            
        except Exception as e:
            logger.error(f"Failed to start UI Abstraction Manager: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop all UI interfaces"""
        try:
            logger.info("Stopping UI Abstraction Manager")
            
            self.is_running = False
            
            # Stop all interfaces
            await self.ui_manager.stop_all()
            
            # Disconnect from orchestrator
            if self.orchestrator_client:
                await self.orchestrator_client.disconnect()
            
            logger.info("UI Abstraction Manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping UI Abstraction Manager: {e}")
    
    async def _connect_to_orchestrator(self) -> None:
        """Connect to core orchestrator"""
        try:
            orchestrator_config = self.config["orchestrator"]
            
            # Create MCP client for orchestrator communication
            self.orchestrator_client = MCPClient()
            
            # Connect to orchestrator (simplified - in real implementation would use proper MCP connection)
            logger.info(f"Connecting to orchestrator at {orchestrator_config['host']}:{orchestrator_config['port']}")
            
            # Set the orchestrator client in UI manager
            self.ui_manager.orchestrator_client = self.orchestrator_client
            
            logger.info("Connected to orchestrator")
            
        except Exception as e:
            logger.error(f"Failed to connect to orchestrator: {e}")
            raise
    
    async def _initialize_interfaces(self) -> None:
        """Initialize all UI interfaces"""
        try:
            # Voice Interface
            if self.config["voice_interface"]["enabled"]:
                voice_config = UIAdapterConfig(
                    interface_type=InterfaceType.VOICE,
                    enabled=True,
                    host=self.config["voice_interface"]["host"],
                    port=self.config["voice_interface"]["port"],
                    max_connections=self.config["voice_interface"]["max_connections"],
                    timeout=self.config["voice_interface"]["timeout"]
                )
                
                voice_interface = VoiceInterface(voice_config)
                self.ui_manager.register_adapter(voice_interface)
                logger.info("Voice interface registered")
            
            # Text Interface
            if self.config["text_interface"]["enabled"]:
                text_config = UIAdapterConfig(
                    interface_type=InterfaceType.TEXT,
                    enabled=True,
                    host=self.config["text_interface"]["host"],
                    port=self.config["text_interface"]["port"],
                    max_connections=self.config["text_interface"]["max_connections"],
                    timeout=self.config["text_interface"]["timeout"],
                    custom_settings={
                        "enable_cli": self.config["text_interface"]["enable_cli"]
                    }
                )
                
                text_interface = TextInterface(text_config)
                self.ui_manager.register_adapter(text_interface)
                logger.info("Text interface registered")
            
            # Web Interface
            if self.config["web_interface"]["enabled"]:
                web_config = UIAdapterConfig(
                    interface_type=InterfaceType.WEB,
                    enabled=True,
                    host=self.config["web_interface"]["host"],
                    port=self.config["web_interface"]["port"],
                    max_connections=self.config["web_interface"]["max_connections"],
                    timeout=self.config["web_interface"]["timeout"],
                    ssl_enabled=self.config["web_interface"]["ssl_enabled"]
                )
                
                web_interface = WebInterface(web_config)
                self.ui_manager.register_adapter(web_interface)
                logger.info("Web interface registered")
            
            # Mobile Interface
            if self.config["mobile_interface"]["enabled"]:
                mobile_config = UIAdapterConfig(
                    interface_type=InterfaceType.MOBILE,
                    enabled=True,
                    host=self.config["mobile_interface"]["host"],
                    port=self.config["mobile_interface"]["port"],
                    max_connections=self.config["mobile_interface"]["max_connections"],
                    timeout=self.config["mobile_interface"]["timeout"],
                    authentication_required=self.config["mobile_interface"]["authentication_required"]
                )
                
                mobile_interface = MobileInterface(mobile_config)
                self.ui_manager.register_adapter(mobile_interface)
                logger.info("Mobile interface registered")
            
        except Exception as e:
            logger.error(f"Failed to initialize interfaces: {e}")
            raise
    
    async def _monitor_connections(self) -> None:
        """Monitor connections and provide statistics"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                stats = self.ui_manager.get_all_stats()
                total_connections = sum(stat.active_connections for stat in stats.values())
                total_messages = sum(stat.messages_sent + stat.messages_received for stat in stats.values())
                
                logger.info(f"UI Statistics - Connections: {total_connections}, Messages: {total_messages}")
                
                # Log per-interface stats
                for interface_type, stat in stats.items():
                    logger.debug(f"{interface_type.value}: {stat.active_connections} active, "
                               f"{stat.messages_sent} sent, {stat.messages_received} received")
                
            except Exception as e:
                logger.error(f"Error monitoring connections: {e}")
    
    async def _health_check(self) -> None:
        """Perform health checks on all interfaces"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                stats = self.ui_manager.get_all_stats()
                
                for interface_type, stat in stats.items():
                    # Check if interface is responsive
                    if stat.uptime > 0 and stat.last_activity:
                        time_since_activity = (asyncio.get_event_loop().time() - stat.last_activity.timestamp())
                        if time_since_activity > 300:  # 5 minutes
                            logger.warning(f"{interface_type.value} interface has been inactive for {time_since_activity:.0f} seconds")
                    
                    # Check error rate
                    total_messages = stat.messages_sent + stat.messages_received
                    if total_messages > 0:
                        error_rate = stat.errors / total_messages
                        if error_rate > 0.1:  # 10% error rate
                            logger.warning(f"{interface_type.value} interface has high error rate: {error_rate:.2%}")
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall status of UI abstraction manager"""
        try:
            stats = self.ui_manager.get_all_stats()
            
            return {
                "status": "running" if self.is_running else "stopped",
                "interfaces": {
                    interface_type.value: {
                        "enabled": stat.interface_type in stats,
                        "active_connections": stat.active_connections,
                        "total_connections": stat.total_connections,
                        "messages_sent": stat.messages_sent,
                        "messages_received": stat.messages_received,
                        "errors": stat.errors,
                        "uptime": stat.uptime,
                        "last_activity": stat.last_activity.isoformat() if stat.last_activity else None
                    }
                    for interface_type, stat in stats.items()
                },
                "total_connections": sum(stat.active_connections for stat in stats.values()),
                "total_messages": sum(stat.messages_sent + stat.messages_received for stat in stats.values()),
                "total_errors": sum(stat.errors for stat in stats.values()),
                "orchestrator_connected": self.orchestrator_client is not None
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


async def main():
    """Main entry point"""
    logger.info("Starting AI-SERVIS UI Abstraction")
    
    # Create and start UI abstraction manager
    ui_manager = UIAbstractionManager()
    
    try:
        await ui_manager.start()
        
        # Keep running
        logger.info("UI Abstraction is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down UI Abstraction")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await ui_manager.stop()


if __name__ == "__main__":
    asyncio.run(main())
