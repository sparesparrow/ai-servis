"""
AI-SERVIS Universal: Integrated Core Orchestrator
Enhanced orchestrator with service discovery, authentication, and advanced NLP
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
import aiohttp
import httpx
from pathlib import Path

# Import our MCP framework
from mcp_framework import (
    MCPServer,
    MCPClient,
    MCPMessage,
    MCPTransport,
    WebSocketTransport,
    HTTPTransport,
    Tool,
    create_tool,
)

# Import our existing modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'service-discovery'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai-auth'))

from enhanced_orchestrator import (
    ServiceInfo, UserContext, SessionContext, IntentResult,
    EnhancedNLPProcessor, ContextManager
)

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ServiceDiscoveryClient:
    """Client for service discovery integration"""
    
    def __init__(self, discovery_host: str = "localhost", discovery_port: int = 8081):
        self.discovery_host = discovery_host
        self.discovery_port = discovery_port
        self.base_url = f"http://{discovery_host}:{discovery_port}"
        self.discovered_services: Dict[str, ServiceInfo] = {}
    
    async def discover_services(self) -> Dict[str, ServiceInfo]:
        """Discover available services"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/discover_services")
                if response.status_code == 200:
                    data = response.json()
                    services = {}
                    
                    for service_data in data.get("services", []):
                        service = ServiceInfo(
                            name=service_data["name"],
                            host=service_data["host"],
                            port=service_data["port"],
                            capabilities=service_data["capabilities"],
                            health_status=service_data.get("health_status", "unknown"),
                            last_seen=datetime.now(),
                            service_type=service_data.get("service_type", "http"),
                            metadata=service_data.get("metadata", {})
                        )
                        services[service.name] = service
                    
                    self.discovered_services = services
                    logger.info(f"Discovered {len(services)} services")
                    return services
                else:
                    logger.error(f"Failed to discover services: {response.status_code}")
                    return {}
        except Exception as e:
            logger.error(f"Error discovering services: {e}")
            return {}
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status of a specific service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/check_service_health")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("health_status", {}).get(service_name, {})
                return {}
        except Exception as e:
            logger.error(f"Error getting service health: {e}")
            return {}


class AuthenticationClient:
    """Client for authentication integration"""
    
    def __init__(self, auth_host: str = "localhost", auth_port: int = 8082):
        self.auth_host = auth_host
        self.auth_port = auth_port
        self.base_url = f"http://{auth_host}:{auth_port}"
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/verify_token",
                    json={"token": token}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("valid"):
                        return data.get("payload")
                return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    async def check_permission(self, token: str, permission: str) -> bool:
        """Check if token has required permission"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/check_permission",
                    json={"token": token, "permission": permission}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("has_permission", False)
                return False
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False


class IntegratedCoreOrchestrator(MCPServer):
    """Integrated Core Orchestrator with service discovery and authentication"""
    
    def __init__(self):
        super().__init__("ai-servis-core-integrated", "3.0.0")
        self.services: Dict[str, ServiceInfo] = {}
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.nlp_processor = EnhancedNLPProcessor()
        self.context_manager = ContextManager()
        
        # Integration clients
        self.service_discovery = ServiceDiscoveryClient()
        self.auth_client = AuthenticationClient()
        
        self.setup_tools()
        self._start_background_tasks()
    
    def setup_tools(self):
        """Setup integrated orchestrator tools"""
        
        # Enhanced voice command processing with authentication
        voice_command_tool = create_tool(
            name="process_voice_command",
            description="Process natural language command with authentication and context awareness",
            schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The voice command text to process"},
                    "session_id": {"type": "string", "description": "Session ID for context management"},
                    "user_id": {"type": "string", "description": "User ID for personalization"},
                    "auth_token": {"type": "string", "description": "JWT authentication token"},
                    "interface_type": {"type": "string", "description": "Interface type (voice, text, web, mobile)", "default": "voice"},
                    "context": {"type": "object", "description": "Additional context information"}
                },
                "required": ["text"]
            },
            handler=self.handle_authenticated_voice_command,
        )
        self.add_tool(voice_command_tool)
        
        # Service discovery integration
        discover_services_tool = create_tool(
            name="discover_services",
            description="Discover and register available services",
            schema={"type": "object", "properties": {}},
            handler=self.handle_discover_services,
        )
        self.add_tool(discover_services_tool)
        
        # Service health monitoring
        service_health_tool = create_tool(
            name="check_service_health",
            description="Check health status of all services",
            schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Optional specific service to check"}
                }
            },
            handler=self.handle_service_health,
        )
        self.add_tool(service_health_tool)
        
        # Intent analysis with context
        analyze_intent_tool = create_tool(
            name="analyze_intent",
            description="Analyze command intent with confidence scores and context",
            schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                    "session_id": {"type": "string", "description": "Session ID for context"},
                    "auth_token": {"type": "string", "description": "Authentication token"}
                },
                "required": ["text"]
            },
            handler=self.handle_analyze_intent,
        )
        self.add_tool(analyze_intent_tool)
        
        # User session management
        create_session_tool = create_tool(
            name="create_session",
            description="Create a new user session",
            schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "interface_type": {"type": "string", "description": "Interface type"},
                    "auth_token": {"type": "string", "description": "Authentication token"}
                },
                "required": ["user_id", "interface_type"]
            },
            handler=self.handle_create_session,
        )
        self.add_tool(create_session_tool)
        
        # Service routing
        route_command_tool = create_tool(
            name="route_command",
            description="Route command to appropriate service",
            schema={
                "type": "object",
                "properties": {
                    "intent": {"type": "string", "description": "Command intent"},
                    "parameters": {"type": "object", "description": "Command parameters"},
                    "session_id": {"type": "string", "description": "Session ID"},
                    "auth_token": {"type": "string", "description": "Authentication token"}
                },
                "required": ["intent", "parameters"]
            },
            handler=self.handle_route_command,
        )
        self.add_tool(route_command_tool)
    
    async def handle_authenticated_voice_command(
        self,
        text: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        auth_token: Optional[str] = None,
        interface_type: str = "voice",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle voice command with authentication"""
        logger.info(f"Processing authenticated command: {text}")
        
        try:
            # Verify authentication if token provided
            user_info = None
            if auth_token:
                user_info = await self.auth_client.verify_token(auth_token)
                if not user_info:
                    return {
                        "error": "Invalid authentication token",
                        "response": "Authentication failed"
                    }
                
                # Use authenticated user ID
                if user_id is None:
                    user_id = user_info.get("username", "anonymous")
            
            # Create session if needed
            if not session_id and user_id:
                session_id = self.context_manager.create_session(user_id, interface_type)
            elif not session_id:
                session_id = self.context_manager.create_session("anonymous", interface_type)
            
            # Get session context
            session_context = self.context_manager.get_session(session_id)
            
            # Parse command with context
            intent_result = await self.nlp_processor.parse_command(text, session_context)
            
            logger.info(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
            
            # Route command
            response = await self._route_authenticated_command(
                intent_result, session_context, context, user_info
            )
            
            # Update context
            if session_context:
                self.context_manager.update_session(
                    session_id,
                    last_intent=intent_result.intent,
                    last_parameters=intent_result.parameters,
                )
                self.context_manager.add_to_history(session_id, text, response)
            
            return {
                "response": response,
                "intent": intent_result.intent,
                "confidence": intent_result.confidence,
                "context_used": intent_result.context_used,
                "alternatives": intent_result.alternatives,
                "session_id": session_id,
                "user_authenticated": user_info is not None
            }
            
        except Exception as e:
            logger.error(f"Error processing authenticated command: {e}")
            return {
                "error": str(e),
                "response": f"Error processing command: {str(e)}",
                "intent": "error",
                "confidence": 0.0,
                "session_id": session_id,
            }
    
    async def handle_discover_services(self) -> Dict[str, Any]:
        """Handle service discovery"""
        try:
            services = await self.service_discovery.discover_services()
            self.services.update(services)
            
            return {
                "message": f"Discovered {len(services)} services",
                "services": {
                    name: {
                        "host": service.host,
                        "port": service.port,
                        "capabilities": service.capabilities,
                        "health_status": service.health_status,
                        "service_type": service.service_type
                    }
                    for name, service in services.items()
                },
                "total_services": len(self.services)
            }
        except Exception as e:
            logger.error(f"Error discovering services: {e}")
            return {"error": str(e)}
    
    async def handle_service_health(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Handle service health check"""
        try:
            if service_name:
                health_data = await self.service_discovery.get_service_health(service_name)
                return {"service": service_name, "health": health_data}
            else:
                # Check all services
                health_results = {}
                for name in self.services.keys():
                    health_data = await self.service_discovery.get_service_health(name)
                    health_results[name] = health_data
                
                return {"health_results": health_results}
        except Exception as e:
            logger.error(f"Error checking service health: {e}")
            return {"error": str(e)}
    
    async def handle_analyze_intent(
        self,
        text: str,
        session_id: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle intent analysis with authentication"""
        try:
            # Verify authentication if token provided
            if auth_token:
                user_info = await self.auth_client.verify_token(auth_token)
                if not user_info:
                    return {"error": "Invalid authentication token"}
            
            # Get session context
            session_context = None
            if session_id:
                session_context = self.context_manager.get_session(session_id)
            
            # Analyze intent
            intent_result = await self.nlp_processor.parse_command(text, session_context)
            
            return {
                "intent": intent_result.intent,
                "confidence": intent_result.confidence,
                "parameters": intent_result.parameters,
                "context_used": intent_result.context_used,
                "alternatives": intent_result.alternatives,
                "original_text": intent_result.original_text,
                "authenticated": auth_token is not None
            }
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {"error": str(e)}
    
    async def handle_create_session(
        self,
        user_id: str,
        interface_type: str,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle session creation with authentication"""
        try:
            # Verify authentication if token provided
            if auth_token:
                user_info = await self.auth_client.verify_token(auth_token)
                if not user_info:
                    return {"error": "Invalid authentication token"}
                
                # Use authenticated user ID
                user_id = user_info.get("username", user_id)
            
            session_id = self.context_manager.create_session(user_id, interface_type)
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "interface_type": interface_type,
                "created_at": datetime.now().isoformat(),
                "authenticated": auth_token is not None
            }
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {"error": str(e)}
    
    async def handle_route_command(
        self,
        intent: str,
        parameters: Dict[str, Any],
        session_id: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle command routing with authentication"""
        try:
            # Verify authentication if token provided
            user_info = None
            if auth_token:
                user_info = await self.auth_client.verify_token(auth_token)
                if not user_info:
                    return {"error": "Invalid authentication token"}
            
            # Get session context
            session_context = None
            if session_id:
                session_context = self.context_manager.get_session(session_id)
            
            # Create intent result
            intent_result = IntentResult(
                intent=intent,
                confidence=1.0,
                parameters=parameters,
                original_text=f"Routed command: {intent}"
            )
            
            # Route command
            response = await self._route_authenticated_command(
                intent_result, session_context, None, user_info
            )
            
            return {
                "response": response,
                "intent": intent,
                "parameters": parameters,
                "session_id": session_id,
                "authenticated": user_info is not None
            }
        except Exception as e:
            logger.error(f"Error routing command: {e}")
            return {"error": str(e)}
    
    async def _route_authenticated_command(
        self,
        intent_result: IntentResult,
        session_context: Optional[SessionContext],
        additional_context: Optional[Dict[str, Any]],
        user_info: Optional[Dict[str, Any]]
    ) -> str:
        """Route command with authentication and enhanced logic"""
        intent = intent_result.intent
        parameters = intent_result.parameters
        
        # Check permissions for sensitive operations
        if user_info and intent in ["system_control", "hardware_control"]:
            required_permission = f"service:{intent.split('_')[0]}"
            # Note: In a real implementation, you would check permissions here
        
        # Handle follow-up commands
        if intent == "follow_up" and session_context:
            return await self._handle_follow_up(intent_result, session_context)
        
        # Low confidence handling
        if intent_result.confidence < 0.3:
            alternatives = [alt[0] for alt in intent_result.alternatives[:2]]
            return f"I'm not sure what you meant. Did you mean: {', '.join(alternatives)}? (confidence: {intent_result.confidence:.2f})"
        
        # Route to appropriate service
        service_mapping = {
            "play_music": "ai-audio-assistant",
            "control_volume": "ai-audio-assistant",
            "switch_audio": "ai-audio-assistant",
            "system_control": "ai-platform-linux",
            "file_operation": "webgrab-server",
            "hardware_control": "hardware-bridge",
            "smart_home": "ai-home-automation",
            "communication": "ai-communications",
            "navigation": "ai-maps-navigation",
        }
        
        service_name = service_mapping.get(intent)
        if not service_name:
            return f"No service available for intent: {intent}"
        
        # Check if service is available
        if service_name not in self.services:
            return f"Service {service_name} not available. Available services: {list(self.services.keys())}"
        
        # Enhanced service call
        result = await self._call_service_enhanced(
            service_name, intent, parameters, session_context, user_info
        )
        return result
    
    async def _handle_follow_up(
        self, intent_result: IntentResult, session_context: SessionContext
    ) -> str:
        """Handle follow-up commands using context"""
        if not session_context.last_intent:
            return "I don't have context for a follow-up. Please be more specific."
        
        # Merge parameters from context
        merged_params = session_context.last_parameters.copy()
        merged_params.update(intent_result.parameters)
        
        # Create new intent result with context
        contextual_intent = IntentResult(
            intent=session_context.last_intent,
            confidence=0.8,
            parameters=merged_params,
            original_text=intent_result.original_text,
            context_used=True,
        )
        
        return await self._route_authenticated_command(
            contextual_intent, session_context, None, None
        )
    
    async def _call_service_enhanced(
        self,
        service_name: str,
        tool_name: str,
        parameters: Dict[str, str],
        session_context: Optional[SessionContext],
        user_info: Optional[Dict[str, Any]]
    ) -> str:
        """Enhanced service call with monitoring and authentication"""
        if service_name not in self.services:
            return f"Service {service_name} not available"
        
        service = self.services[service_name]
        start_time = time.time()
        
        try:
            # Add session context to parameters if available
            if session_context:
                parameters["session_id"] = session_context.session_id
                parameters["user_id"] = session_context.user_id
            
            # Add user info if authenticated
            if user_info:
                parameters["user_info"] = json.dumps(user_info)
            
            # Call service based on type
            if service.service_type == "mcp":
                result = await self._call_mcp_service(service_name, tool_name, parameters)
            elif service.service_type == "http":
                result = await self._call_http_service(service, tool_name, parameters)
            else:
                result = f"Unsupported service type: {service.service_type}"
            
            # Update service metrics
            response_time = time.time() - start_time
            service.response_time = response_time
            service.health_status = "healthy"
            service.last_seen = datetime.now()
            
            # Update session context
            if session_context:
                self.context_manager.update_session(
                    session_context.session_id, last_used_service=service_name
                )
            
            return result
            
        except Exception as e:
            # Update error metrics
            service.error_count += 1
            service.health_status = "error"
            
            logger.error(f"Error calling service {service_name}: {e}")
            return f"Error calling service {service_name}: {str(e)}"
    
    async def _call_mcp_service(
        self, service_name: str, tool_name: str, parameters: Dict[str, str]
    ) -> str:
        """Call MCP service"""
        client = self.mcp_clients.get(service_name)
        if not client:
            return f"MCP client not available for {service_name}"
        
        result = await client.call_tool(tool_name, parameters)
        return f"Service {service_name} responded: {result}"
    
    async def _call_http_service(
        self, service: ServiceInfo, tool_name: str, parameters: Dict[str, str]
    ) -> str:
        """Call HTTP service"""
        url = f"http://{service.host}:{service.port}/api/{tool_name}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=parameters)
            if response.status_code == 200:
                result = response.json()
                return result.get("message", "HTTP service completed")
            else:
                return f"HTTP error: {response.status_code}"
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        asyncio.create_task(self._periodic_service_discovery())
        asyncio.create_task(self._periodic_cleanup())
        logger.info("Background tasks started")
    
    async def _periodic_service_discovery(self):
        """Periodic service discovery"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                await self.service_discovery.discover_services()
            except Exception as e:
                logger.error(f"Error in service discovery task: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                self.context_manager.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")


async def main():
    """Main entry point for integrated orchestrator"""
    logger.info("Starting AI-SERVIS Integrated Core Orchestrator")
    
    # Create integrated orchestrator
    orchestrator = IntegratedCoreOrchestrator()
    
    # Initial service discovery
    await orchestrator.handle_discover_services()
    
    # Start HTTP server
    from aiohttp import web
    
    app = web.Application()
    
    async def handle_command(request):
        """HTTP endpoint for command processing"""
        data = await request.json()
        result = await orchestrator.handle_authenticated_voice_command(**data)
        return web.json_response(result)
    
    async def handle_discovery(request):
        """HTTP endpoint for service discovery"""
        result = await orchestrator.handle_discover_services()
        return web.json_response(result)
    
    async def handle_health(request):
        """HTTP endpoint for health checks"""
        service_name = request.query.get("service")
        result = await orchestrator.handle_service_health(service_name)
        return web.json_response(result)
    
    app.router.add_post("/api/command", handle_command)
    app.router.add_get("/api/discover", handle_discovery)
    app.router.add_get("/api/health", handle_health)
    
    # CORS support
    async def add_cors_headers(request, response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
    
    app.middlewares.append(add_cors_headers)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    
    logger.info("Integrated Core Orchestrator started on port 8080")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Integrated Core Orchestrator")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
