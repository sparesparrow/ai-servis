"""
AI-SERVIS Universal: Service Discovery MCP Server
Handles automatic service registration and health checking
"""

import asyncio
import logging
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp
import websockets
import asyncio_mqtt as mqtt
from zeroconf import ServiceInfo, Zeroconf, ServiceListener
import socket

# Import our MCP framework
from mcp_framework import (
    MCPServer,
    MCPClient,
    MCPMessage,
    MCPTransport,
    WebSocketTransport,
    Tool,
    create_tool,
)


# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceEntry:
    """Service registration entry"""

    name: str
    host: str
    port: int
    capabilities: List[str]
    health_endpoint: Optional[str] = None
    last_heartbeat: datetime = None
    status: str = "unknown"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class MDNSServiceListener(ServiceListener):
    """mDNS service listener for automatic discovery"""

    def __init__(self, registry: 'ServiceRegistry'):
        self.registry = registry

    def add_service(self, zeroconf, type, name):
        """Called when a new service is discovered"""
        info = zeroconf.get_service_info(type, name)
        if info:
            service_name = name.split('.')[0]
            host = socket.inet_ntoa(info.addresses[0]) if info.addresses else "localhost"
            port = info.port
            capabilities = []
            
            # Extract capabilities from TXT records
            if info.properties:
                for key, value in info.properties.items():
                    if key.decode() == 'capabilities':
                        capabilities = value.decode().split(',')
            
            self.registry.register_service(
                name=service_name,
                host=host,
                port=port,
                capabilities=capabilities,
                metadata={'discovery_method': 'mdns', 'service_type': type}
            )

    def remove_service(self, zeroconf, type, name):
        """Called when a service is removed"""
        service_name = name.split('.')[0]
        self.registry.unregister_service(service_name)

    def update_service(self, zeroconf, type, name):
        """Called when a service is updated"""
        pass


class MQTTServiceRegistry:
    """MQTT-based service registry"""

    def __init__(self, mqtt_broker: str = "localhost", mqtt_port: int = 1883):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.client = None
        self.registry = None

    async def start(self, registry: 'ServiceRegistry'):
        """Start MQTT service registry"""
        self.registry = registry
        self.client = mqtt.Client(hostname=self.mqtt_broker, port=self.mqtt_port)
        
        async with self.client:
            await self.client.subscribe("ai-servis/services/+/register")
            await self.client.subscribe("ai-servis/services/+/heartbeat")
            await self.client.subscribe("ai-servis/services/+/unregister")
            
            async for message in self.client.messages:
                await self._handle_mqtt_message(message)

    async def _handle_mqtt_message(self, message):
        """Handle incoming MQTT messages"""
        try:
            topic_parts = message.topic.value.split('/')
            service_name = topic_parts[2]
            message_type = topic_parts[3]
            
            if message_type == "register":
                data = json.loads(message.payload.decode())
                self.registry.register_service(
                    name=service_name,
                    host=data.get('host', 'localhost'),
                    port=data.get('port', 8080),
                    capabilities=data.get('capabilities', []),
                    health_endpoint=data.get('health_endpoint'),
                    metadata={'discovery_method': 'mqtt', **data.get('metadata', {})}
                )
            elif message_type == "heartbeat":
                await self.registry.heartbeat(service_name)
            elif message_type == "unregister":
                self.registry.unregister_service(service_name)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    async def publish_service_registration(self, service: ServiceEntry):
        """Publish service registration to MQTT"""
        if self.client:
            topic = f"ai-servis/services/{service.name}/register"
            data = {
                'host': service.host,
                'port': service.port,
                'capabilities': service.capabilities,
                'health_endpoint': service.health_endpoint,
                'metadata': service.metadata
            }
            await self.client.publish(topic, json.dumps(data))


class ServiceRegistry:
    """Service registry for automatic discovery"""

    def __init__(self):
        self.services: Dict[str, ServiceEntry] = {}
        self.heartbeat_timeout = timedelta(
            seconds=30
        )  # Services must heartbeat every 30s
        self.mdns_zeroconf = None
        self.mdns_listener = None
        self.mqtt_registry = None
        
        # Configuration management
        self.config = {
            "heartbeat_timeout_seconds": 30,
            "cleanup_interval_seconds": 60,
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mdns_service_type": "_ai-servis._tcp.local.",
            "enable_mdns": True,
            "enable_mqtt": True,
            "log_level": "INFO"
        }

    def register_service(
        self,
        name: str,
        host: str,
        port: int,
        capabilities: List[str],
        health_endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Register a new service"""
        if name in self.services:
            logger.warning(f"Service {name} already registered, updating...")
            return False

        entry = ServiceEntry(
            name=name,
            host=host,
            port=port,
            capabilities=capabilities,
            health_endpoint=health_endpoint,
            metadata=metadata or {},
        )

        self.services[name] = entry
        logger.info(f"Registered service: {name} at {host}:{port}")
        return True

    def update_service(self, name: str, **kwargs) -> bool:
        """Update service information"""
        if name not in self.services:
            return False

        entry = self.services[name]
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        entry.last_heartbeat = datetime.now()
        return True

    def unregister_service(self, name: str) -> bool:
        """Unregister a service"""
        if name in self.services:
            del self.services[name]
            logger.info(f"Unregistered service: {name}")
            return True
        return False

    def get_service(self, name: str) -> Optional[ServiceEntry]:
        """Get service information"""
        return self.services.get(name)

    def list_services(
        self, capability_filter: Optional[str] = None
    ) -> List[ServiceEntry]:
        """List all registered services"""
        services = list(self.services.values())

        if capability_filter:
            services = [s for s in services if capability_filter in s.capabilities]

        return services

    def check_health(self) -> Dict[str, str]:
        """Check health of all services"""
        results = {}
        now = datetime.now()

        for name, service in self.services.items():
            if now - service.last_heartbeat > self.heartbeat_timeout:
                service.status = "unhealthy"
            else:
                service.status = "healthy"
            results[name] = service.status

        return results

    async def heartbeat(self, name: str) -> bool:
        """Process heartbeat from service"""
        if name in self.services:
            self.services[name].last_heartbeat = datetime.now()
            self.services[name].status = "healthy"
            return True
        return False

    def cleanup_stale_services(self):
        """Remove services that haven't sent heartbeats"""
        now = datetime.now()
        stale_services = []

        for name, service in self.services.items():
            if now - service.last_heartbeat > self.heartbeat_timeout * 2:
                stale_services.append(name)

        for name in stale_services:
            logger.warning(f"Removing stale service: {name}")
            del self.services[name]

    def start_mdns_discovery(self):
        """Start mDNS service discovery"""
        try:
            self.mdns_zeroconf = Zeroconf()
            self.mdns_listener = MDNSServiceListener(self)
            
            # Listen for AI-SERVIS services
            self.mdns_zeroconf.add_service_listener("_ai-servis._tcp.local.", self.mdns_listener)
            logger.info("Started mDNS service discovery")
        except Exception as e:
            logger.error(f"Failed to start mDNS discovery: {e}")

    def stop_mdns_discovery(self):
        """Stop mDNS service discovery"""
        if self.mdns_zeroconf:
            self.mdns_zeroconf.close()
            logger.info("Stopped mDNS service discovery")

    async def start_mqtt_discovery(self, mqtt_broker: str = "localhost", mqtt_port: int = 1883):
        """Start MQTT service discovery"""
        try:
            self.mqtt_registry = MQTTServiceRegistry(mqtt_broker, mqtt_port)
            # Start MQTT registry in background task
            asyncio.create_task(self.mqtt_registry.start(self))
            logger.info(f"Started MQTT service discovery on {mqtt_broker}:{mqtt_port}")
        except Exception as e:
            logger.error(f"Failed to start MQTT discovery: {e}")

    async def publish_to_mqtt(self, service: ServiceEntry):
        """Publish service registration to MQTT"""
        if self.mqtt_registry:
            await self.mqtt_registry.publish_service_registration(service)

    def get_config(self, key: str) -> Any:
        """Get configuration value"""
        return self.config.get(key)

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self.config.copy()

    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value"""
        if key in self.config:
            self.config[key] = value
            # Update related settings if needed
            if key == "heartbeat_timeout_seconds":
                self.heartbeat_timeout = timedelta(seconds=value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")

    def reset_config(self, key: str) -> None:
        """Reset configuration to default"""
        defaults = {
            "heartbeat_timeout_seconds": 30,
            "cleanup_interval_seconds": 60,
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mdns_service_type": "_ai-servis._tcp.local.",
            "enable_mdns": True,
            "enable_mqtt": True,
            "log_level": "INFO"
        }
        if key in defaults:
            self.set_config(key, defaults[key])
        else:
            raise ValueError(f"Unknown configuration key: {key}")

    def reset_all_config(self) -> None:
        """Reset all configuration to defaults"""
        defaults = {
            "heartbeat_timeout_seconds": 30,
            "cleanup_interval_seconds": 60,
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mdns_service_type": "_ai-servis._tcp.local.",
            "enable_mdns": True,
            "enable_mqtt": True,
            "log_level": "INFO"
        }
        for key, value in defaults.items():
            self.config[key] = value
        self.heartbeat_timeout = timedelta(seconds=self.config["heartbeat_timeout_seconds"])


class ServiceDiscoveryMCP(MCPServer):
    """Service Discovery MCP Server"""

    def __init__(self):
        super().__init__("service-discovery", "1.0.0")
        self.registry = ServiceRegistry()
        self.setup_tools()
        self._start_cleanup_task()
        self._start_discovery_services()

    def setup_tools(self):
        """Setup service discovery tools"""

        # Service registration
        register_tool = create_tool(
            name="register_service",
            description="Register a new service with the discovery system",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Service name"},
                    "host": {"type": "string", "description": "Service host"},
                    "port": {"type": "integer", "description": "Service port"},
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of service capabilities",
                    },
                    "health_endpoint": {
                        "type": "string",
                        "description": "Health check endpoint",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata",
                    },
                },
                "required": ["name", "host", "port", "capabilities"],
            },
            handler=self.handle_register_service,
        )
        self.add_tool(register_tool)

        # Service discovery
        discover_tool = create_tool(
            name="discover_services",
            description="Discover available services",
            schema={
                "type": "object",
                "properties": {
                    "capability": {
                        "type": "string",
                        "description": "Filter by capability",
                    }
                },
            },
            handler=self.handle_discover_services,
        )
        self.add_tool(discover_tool)

        # Service heartbeat
        heartbeat_tool = create_tool(
            name="service_heartbeat",
            description="Send heartbeat to keep service alive",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Service name"}
                },
                "required": ["name"],
            },
            handler=self.handle_heartbeat,
        )
        self.add_tool(heartbeat_tool)

        # Health check
        health_tool = create_tool(
            name="check_service_health",
            description="Check health status of all services",
            schema={"type": "object", "properties": {}},
            handler=self.handle_health_check,
        )
        self.add_tool(health_tool)

        # Service monitoring
        monitor_tool = create_tool(
            name="monitor_services",
            description="Get detailed monitoring information for services",
            schema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Optional service name to monitor specific service"
                    }
                }
            },
            handler=self.handle_monitor_services,
        )
        self.add_tool(monitor_tool)

        # Service lifecycle management
        unregister_tool = create_tool(
            name="unregister_service",
            description="Unregister a service from the registry",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Service name to unregister"}
                },
                "required": ["name"],
            },
            handler=self.handle_unregister_service,
        )
        self.add_tool(unregister_tool)

        # Service restart
        restart_tool = create_tool(
            name="restart_service",
            description="Restart a service (unregister and re-register)",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Service name to restart"},
                    "host": {"type": "string", "description": "New host (optional)"},
                    "port": {"type": "integer", "description": "New port (optional)"},
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New capabilities (optional)"
                    }
                },
                "required": ["name"],
            },
            handler=self.handle_restart_service,
        )
        self.add_tool(restart_tool)

        # Configuration management
        config_tool = create_tool(
            name="manage_configuration",
            description="Manage service discovery configuration",
            schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get", "set", "reset"],
                        "description": "Configuration action"
                    },
                    "key": {
                        "type": "string",
                        "description": "Configuration key (for get/set actions)"
                    },
                    "value": {
                        "type": "string",
                        "description": "Configuration value (for set action)"
                    }
                },
                "required": ["action"],
            },
            handler=self.handle_configuration,
        )
        self.add_tool(config_tool)

    async def handle_register_service(
        self,
        name: str,
        host: str,
        port: int,
        capabilities: List[str],
        health_endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle service registration"""
        try:
            success = self.registry.register_service(
                name, host, port, capabilities, health_endpoint, metadata
            )
            if success:
                # Publish to MQTT if available
                service = self.registry.services.get(name)
                if service:
                    await self.registry.publish_to_mqtt(service)
                return f"Service {name} registered successfully"
            else:
                return f"Service {name} already exists"
        except Exception as e:
            logger.error(f"Error registering service: {e}")
            return f"Registration failed: {str(e)}"

    async def handle_discover_services(
        self, capability: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle service discovery"""
        try:
            services = self.registry.list_services(capability)
            return {
                "services": [
                    {
                        "name": s.name,
                        "host": s.host,
                        "port": s.port,
                        "capabilities": s.capabilities,
                        "status": s.status,
                        "last_heartbeat": s.last_heartbeat.isoformat(),
                        "metadata": s.metadata,
                    }
                    for s in services
                ],
                "total": len(services),
            }
        except Exception as e:
            logger.error(f"Error discovering services: {e}")
            return {"error": str(e)}

    async def handle_heartbeat(self, name: str) -> str:
        """Handle service heartbeat"""
        try:
            success = await self.registry.heartbeat(name)
            if success:
                return f"Heartbeat received for {name}"
            else:
                return f"Service {name} not found"
        except Exception as e:
            logger.error(f"Error processing heartbeat: {e}")
            return f"Heartbeat failed: {str(e)}"

    async def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check request"""
        try:
            health_status = self.registry.check_health()
            total_services = len(self.registry.services)
            healthy_count = sum(1 for s in health_status.values() if s == "healthy")
            
            return {
                "status": "healthy" if healthy_count == total_services else "degraded",
                "summary": {
                    "total_services": total_services,
                    "healthy_services": healthy_count,
                    "unhealthy_services": total_services - healthy_count,
                    "health_percentage": round((healthy_count / total_services * 100) if total_services > 0 else 100, 2)
                },
                "health_status": health_status,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    async def handle_monitor_services(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Handle service monitoring request"""
        try:
            if service_name:
                # Monitor specific service
                if service_name not in self.registry.services:
                    return {"error": f"Service '{service_name}' not found"}
                
                service = self.registry.services[service_name]
                health_status = self.registry.check_service_health(service_name)
                
                return {
                    "service": {
                        "name": service.name,
                        "host": service.host,
                        "port": service.port,
                        "capabilities": service.capabilities,
                        "health_endpoint": service.health_endpoint,
                        "last_heartbeat": service.last_heartbeat.isoformat() if service.last_heartbeat else None,
                        "registered_at": service.registered_at.isoformat(),
                        "metadata": service.metadata
                    },
                    "health": health_status,
                    "uptime": str(datetime.now() - service.registered_at),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Monitor all services
                services_info = []
                for name, service in self.registry.services.items():
                    health_status = self.registry.check_service_health(name)
                    services_info.append({
                        "name": service.name,
                        "host": service.host,
                        "port": service.port,
                        "capabilities": service.capabilities,
                        "health": health_status,
                        "last_heartbeat": service.last_heartbeat.isoformat() if service.last_heartbeat else None,
                        "uptime": str(datetime.now() - service.registered_at),
                        "registered_at": service.registered_at.isoformat()
                    })
                
                return {
                    "services": services_info,
                    "total_services": len(services_info),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error monitoring services: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def handle_unregister_service(self, name: str) -> str:
        """Handle service unregistration"""
        try:
            if name not in self.registry.services:
                return f"Service {name} not found"
            
            self.registry.unregister_service(name)
            return f"Service {name} unregistered successfully"
        except Exception as e:
            logger.error(f"Error unregistering service: {e}")
            return f"Unregistration failed: {str(e)}"

    async def handle_restart_service(
        self,
        name: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        capabilities: Optional[List[str]] = None
    ) -> str:
        """Handle service restart"""
        try:
            if name not in self.registry.services:
                return f"Service {name} not found"
            
            # Get current service info
            current_service = self.registry.services[name]
            
            # Use provided values or keep current ones
            new_host = host or current_service.host
            new_port = port or current_service.port
            new_capabilities = capabilities or current_service.capabilities
            new_health_endpoint = current_service.health_endpoint
            new_metadata = current_service.metadata
            
            # Unregister and re-register
            self.registry.unregister_service(name)
            success = self.registry.register_service(
                name, new_host, new_port, new_capabilities, new_health_endpoint, new_metadata
            )
            
            if success:
                # Publish to MQTT if available
                service = self.registry.services.get(name)
                if service:
                    await self.registry.publish_to_mqtt(service)
                return f"Service {name} restarted successfully"
            else:
                return f"Failed to restart service {name}"
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return f"Restart failed: {str(e)}"

    async def handle_configuration(
        self,
        action: str,
        key: Optional[str] = None,
        value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle configuration management"""
        try:
            if action == "get":
                if key:
                    # Get specific configuration value
                    config_value = self.registry.get_config(key)
                    return {"key": key, "value": config_value}
                else:
                    # Get all configuration
                    return {"configuration": self.registry.get_all_config()}
            
            elif action == "set":
                if not key or value is None:
                    return {"error": "Key and value are required for set action"}
                
                self.registry.set_config(key, value)
                return {"message": f"Configuration {key} set to {value}"}
            
            elif action == "reset":
                if key:
                    # Reset specific configuration to default
                    self.registry.reset_config(key)
                    return {"message": f"Configuration {key} reset to default"}
                else:
                    # Reset all configuration to defaults
                    self.registry.reset_all_config()
                    return {"message": "All configuration reset to defaults"}
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error managing configuration: {e}")
            return {"error": str(e)}

    def _start_cleanup_task(self):
        """Start periodic cleanup task"""
        asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Periodic cleanup of stale services"""
        while True:
            try:
                self.registry.cleanup_stale_services()
                await asyncio.sleep(60)  # Clean up every minute
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    def _start_discovery_services(self):
        """Start mDNS and MQTT discovery services"""
        # Start mDNS discovery
        self.registry.start_mdns_discovery()
        
        # Start MQTT discovery in background
        async def start_mqtt():
            await self.registry.start_mqtt_discovery()
        
        asyncio.create_task(start_mqtt())


async def main():
    """Main entry point for service discovery"""
    logger.info("Starting Service Discovery MCP Server")

    # Create service discovery server
    discovery_server = ServiceDiscoveryMCP()

    # Start WebSocket server for MCP connections
    async def handle_websocket(websocket, path):
        """Handle WebSocket connections"""
        logger.info(f"New WebSocket connection: {websocket.remote_address}")
        transport = WebSocketTransport(websocket)

        try:
            await discovery_server.serve(transport)
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")

    # Start WebSocket server
    port = int(os.getenv("DISCOVERY_PORT", 8090))
    start_server = websockets.serve(handle_websocket, "0.0.0.0", port)

    logger.info(f"Service Discovery MCP Server listening on port {port}")

    try:
        await start_server
        # Keep the server running
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down Service Discovery MCP Server")


if __name__ == "__main__":
    asyncio.run(main())
