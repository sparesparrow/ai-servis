"""
Mobile Interface Bridge for AI-SERVIS
Handles mobile app communication via REST API and WebSocket
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from aiohttp import web, web_request
import jwt
from cryptography.fernet import Fernet

from ui_models import (
    UIAdapter, UIAdapterConfig, InterfaceType, MessageType,
    CommandMessage, ResponseMessage, StatusMessage, ErrorMessage, 
    NotificationMessage, UIMessage
)

logger = logging.getLogger(__name__)


class MobileInterface(UIAdapter):
    """Mobile interface adapter with REST API and WebSocket support"""
    
    def __init__(self, config: UIAdapterConfig):
        super().__init__(config)
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.app = None
        self.runner = None
        self.site = None
        self.device_registry: Dict[str, Dict[str, Any]] = {}
        self.push_notifications = PushNotificationService()
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    async def start(self) -> None:
        """Start mobile interface server"""
        if not self.config.enabled:
            return
        
        try:
            # Create aiohttp app
            self.app = web.Application()
            
            # Setup routes
            self._setup_routes()
            
            # Setup middleware
            self._setup_middleware()
            
            # Start server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(
                self.runner,
                self.config.host,
                self.config.port or 8084
            )
            await self.site.start()
            
            self.is_running = True
            logger.info(f"Mobile interface started on {self.config.host}:{self.config.port or 8084}")
            
        except Exception as e:
            logger.error(f"Failed to start mobile interface: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop mobile interface server"""
        self.is_running = False
        
        if self.site:
            await self.site.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        self.connections.clear()
        self.device_registry.clear()
        logger.info("Mobile interface stopped")
    
    async def send_message(self, message: UIMessage, connection_id: Optional[str] = None) -> bool:
        """Send message to mobile interface"""
        try:
            if connection_id and connection_id in self.connections:
                connection = self.connections[connection_id]
                device_id = connection.get("device_id")
                
                if device_id and device_id in self.device_registry:
                    device = self.device_registry[device_id]
                    
                    # Send push notification if device supports it
                    if device.get("push_token"):
                        await self.push_notifications.send_notification(
                            device["push_token"],
                            message
                        )
                    
                    # Send via WebSocket if connected
                    if connection.get("websocket"):
                        await self._send_websocket_message(connection_id, message)
                    
                    self.stats.messages_sent += 1
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error sending message to mobile interface: {e}")
            self.stats.errors += 1
            return False
    
    async def broadcast_message(self, message: UIMessage) -> int:
        """Broadcast message to all mobile connections"""
        sent_count = 0
        
        for connection_id, connection in self.connections.items():
            try:
                device_id = connection.get("device_id")
                if device_id and device_id in self.device_registry:
                    device = self.device_registry[device_id]
                    
                    # Send push notification
                    if device.get("push_token"):
                        await self.push_notifications.send_notification(
                            device["push_token"],
                            message
                        )
                    
                    # Send via WebSocket
                    if connection.get("websocket"):
                        await self._send_websocket_message(connection_id, message)
                    
                    sent_count += 1
                    self.stats.messages_sent += 1
                    
            except Exception as e:
                logger.error(f"Error broadcasting to mobile connection {connection_id}: {e}")
                self.stats.errors += 1
        
        return sent_count
    
    def _setup_routes(self) -> None:
        """Setup HTTP routes"""
        # Device management
        self.app.router.add_post('/api/mobile/register', self._handle_device_registration)
        self.app.router.add_post('/api/mobile/unregister', self._handle_device_unregistration)
        self.app.router.add_get('/api/mobile/devices', self._handle_list_devices)
        
        # Command handling
        self.app.router.add_post('/api/mobile/command', self._handle_mobile_command)
        self.app.router.add_get('/api/mobile/status', self._handle_mobile_status)
        
        # Push notifications
        self.app.router.add_post('/api/mobile/push/register', self._handle_push_registration)
        self.app.router.add_post('/api/mobile/push/unregister', self._handle_push_unregistration)
        
        # WebSocket for real-time communication
        self.app.router.add_get('/api/mobile/ws', self._handle_websocket)
        
        # Health check
        self.app.router.add_get('/api/mobile/health', self._handle_health)
        
        # Add CORS middleware
        self.app.middlewares.append(self._cors_middleware)
    
    def _setup_middleware(self) -> None:
        """Setup middleware"""
        # Authentication middleware
        self.app.middlewares.append(self._auth_middleware)
        # Logging middleware
        self.app.middlewares.append(self._logging_middleware)
    
    async def _cors_middleware(self, request: web_request.Request, handler):
        """CORS middleware"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Device-ID'
        return response
    
    async def _auth_middleware(self, request: web_request.Request, handler):
        """Authentication middleware"""
        # Skip auth for certain endpoints
        if request.path in ['/api/mobile/register', '/api/mobile/health']:
            return await handler(request)
        
        # Check for device ID in headers
        device_id = request.headers.get('X-Device-ID')
        if not device_id:
            return web.json_response({
                "error": "Device ID required"
            }, status=401)
        
        # Verify device is registered
        if device_id not in self.device_registry:
            return web.json_response({
                "error": "Device not registered"
            }, status=401)
        
        # Add device info to request
        request['device'] = self.device_registry[device_id]
        return await handler(request)
    
    async def _logging_middleware(self, request: web_request.Request, handler):
        """Logging middleware"""
        start_time = datetime.now()
        
        try:
            response = await handler(request)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{request.method} {request.path} - {response.status} ({duration:.3f}s)")
            return response
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{request.method} {request.path} - ERROR ({duration:.3f}s): {e}")
            raise
    
    async def _handle_device_registration(self, request: web_request.Request) -> web.Response:
        """Handle device registration"""
        try:
            data = await request.json()
            device_id = data.get("device_id")
            device_info = data.get("device_info", {})
            
            if not device_id:
                return web.json_response({
                    "error": "Device ID required"
                }, status=400)
            
            # Register device
            self.device_registry[device_id] = {
                "device_id": device_id,
                "device_info": device_info,
                "registered_at": datetime.now(),
                "last_seen": datetime.now(),
                "status": "active",
                "push_token": None,
                "websocket_connected": False
            }
            
            # Create connection
            connection_id = str(uuid.uuid4())
            self.connections[connection_id] = {
                "device_id": device_id,
                "user_id": device_info.get("user_id", "anonymous"),
                "session_id": str(uuid.uuid4()),
                "connected_at": datetime.now(),
                "last_activity": datetime.now(),
                "websocket": None
            }
            
            await self.handle_connection(connection_id)
            
            return web.json_response({
                "success": True,
                "device_id": device_id,
                "connection_id": connection_id,
                "message": "Device registered successfully"
            })
            
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_device_unregistration(self, request: web_request.Request) -> web.Response:
        """Handle device unregistration"""
        try:
            data = await request.json()
            device_id = data.get("device_id")
            
            if not device_id:
                return web.json_response({
                    "error": "Device ID required"
                }, status=400)
            
            # Remove device from registry
            if device_id in self.device_registry:
                del self.device_registry[device_id]
            
            # Remove connections for this device
            connections_to_remove = []
            for conn_id, conn_data in self.connections.items():
                if conn_data.get("device_id") == device_id:
                    connections_to_remove.append(conn_id)
            
            for conn_id in connections_to_remove:
                await self._handle_disconnection(conn_id)
            
            return web.json_response({
                "success": True,
                "message": "Device unregistered successfully"
            })
            
        except Exception as e:
            logger.error(f"Error unregistering device: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_list_devices(self, request: web_request.Request) -> web.Response:
        """Handle list devices request"""
        try:
            devices = []
            for device_id, device_info in self.device_registry.items():
                devices.append({
                    "device_id": device_id,
                    "device_info": device_info.get("device_info", {}),
                    "registered_at": device_info.get("registered_at").isoformat(),
                    "last_seen": device_info.get("last_seen").isoformat(),
                    "status": device_info.get("status"),
                    "websocket_connected": device_info.get("websocket_connected", False)
                })
            
            return web.json_response({
                "devices": devices,
                "total": len(devices)
            })
            
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_mobile_command(self, request: web_request.Request) -> web.Response:
        """Handle mobile command"""
        try:
            data = await request.json()
            command = data.get("command", "")
            context = data.get("context", {})
            
            device = request.get("device", {})
            device_id = device.get("device_id")
            
            # Find connection for this device
            connection_id = None
            for conn_id, conn_data in self.connections.items():
                if conn_data.get("device_id") == device_id:
                    connection_id = conn_id
                    break
            
            if not connection_id:
                return web.json_response({
                    "error": "Device not connected"
                }, status=400)
            
            # Create command message
            command_message = CommandMessage(
                id=str(uuid.uuid4()),
                interface_type=InterfaceType.MOBILE,
                user_id=device.get("user_id", "anonymous"),
                session_id=self.connections[connection_id]["session_id"],
                command=command,
                context=context,
                data={"connection_id": connection_id, "device_id": device_id}
            )
            
            # Handle the command
            await self.handle_message(command_message, connection_id)
            
            return web.json_response({
                "success": True,
                "message_id": command_message.id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling mobile command: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_mobile_status(self, request: web_request.Request) -> web.Response:
        """Handle mobile status request"""
        try:
            stats = self.get_stats()
            return web.json_response({
                "status": "running",
                "stats": stats.dict(),
                "devices": len(self.device_registry),
                "connections": len(self.connections),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error handling mobile status: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_push_registration(self, request: web_request.Request) -> web.Response:
        """Handle push notification registration"""
        try:
            data = await request.json()
            device_id = data.get("device_id")
            push_token = data.get("push_token")
            platform = data.get("platform", "unknown")
            
            if not device_id or not push_token:
                return web.json_response({
                    "error": "Device ID and push token required"
                }, status=400)
            
            if device_id in self.device_registry:
                self.device_registry[device_id]["push_token"] = push_token
                self.device_registry[device_id]["platform"] = platform
                
                return web.json_response({
                    "success": True,
                    "message": "Push token registered successfully"
                })
            else:
                return web.json_response({
                    "error": "Device not registered"
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error registering push token: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_push_unregistration(self, request: web_request.Request) -> web.Response:
        """Handle push notification unregistration"""
        try:
            data = await request.json()
            device_id = data.get("device_id")
            
            if not device_id:
                return web.json_response({
                    "error": "Device ID required"
                }, status=400)
            
            if device_id in self.device_registry:
                self.device_registry[device_id]["push_token"] = None
                
                return web.json_response({
                    "success": True,
                    "message": "Push token unregistered successfully"
                })
            else:
                return web.json_response({
                    "error": "Device not registered"
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error unregistering push token: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_websocket(self, request: web_request.Request) -> web.WebSocketResponse:
        """Handle WebSocket connection"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Get device ID from query parameters
        device_id = request.query.get('device_id')
        if not device_id:
            await ws.close(code=4000, message=b'Device ID required')
            return ws
        
        if device_id not in self.device_registry:
            await ws.close(code=4001, message=b'Device not registered')
            return ws
        
        # Find or create connection
        connection_id = None
        for conn_id, conn_data in self.connections.items():
            if conn_data.get("device_id") == device_id:
                connection_id = conn_id
                break
        
        if not connection_id:
            connection_id = str(uuid.uuid4())
            self.connections[connection_id] = {
                "device_id": device_id,
                "user_id": self.device_registry[device_id].get("user_id", "anonymous"),
                "session_id": str(uuid.uuid4()),
                "connected_at": datetime.now(),
                "last_activity": datetime.now(),
                "websocket": ws
            }
            await self.handle_connection(connection_id)
        else:
            self.connections[connection_id]["websocket"] = ws
        
        # Update device registry
        self.device_registry[device_id]["websocket_connected"] = True
        self.device_registry[device_id]["last_seen"] = datetime.now()
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_websocket_message(connection_id, data)
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON"
                        }))
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Update device registry
            if device_id in self.device_registry:
                self.device_registry[device_id]["websocket_connected"] = False
            
            # Clear WebSocket reference
            if connection_id in self.connections:
                self.connections[connection_id]["websocket"] = None
            
            await self._handle_disconnection(connection_id)
        
        return ws
    
    async def _handle_websocket_message(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle WebSocket message"""
        try:
            message_type = data.get("type")
            
            if message_type == "command":
                command = data.get("command", "")
                context = data.get("context", {})
                
                connection = self.connections[connection_id]
                device_id = connection.get("device_id")
                
                # Create command message
                command_message = CommandMessage(
                    id=str(uuid.uuid4()),
                    interface_type=InterfaceType.MOBILE,
                    user_id=connection.get("user_id"),
                    session_id=connection.get("session_id"),
                    command=command,
                    context=context,
                    data={"connection_id": connection_id, "device_id": device_id}
                )
                
                # Handle the command
                await self.handle_message(command_message, connection_id)
                
            elif message_type == "heartbeat":
                # Update last activity
                self.connections[connection_id]["last_activity"] = datetime.now()
                device_id = self.connections[connection_id].get("device_id")
                if device_id in self.device_registry:
                    self.device_registry[device_id]["last_seen"] = datetime.now()
                
                # Send heartbeat response
                heartbeat_response = {
                    "type": "heartbeat_response",
                    "timestamp": datetime.now().isoformat()
                }
                
                ws = self.connections[connection_id].get("websocket")
                if ws:
                    await ws.send_str(json.dumps(heartbeat_response))
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            self.stats.errors += 1
    
    async def _handle_health(self, request: web_request.Request) -> web.Response:
        """Handle health check"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _send_websocket_message(self, connection_id: str, message: UIMessage) -> None:
        """Send WebSocket message"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            ws = connection.get("websocket")
            if ws:
                try:
                    await ws.send_str(json.dumps(message.dict()))
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
    
    async def _handle_disconnection(self, connection_id: str) -> None:
        """Handle connection disconnection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        await self.handle_disconnection(connection_id)


class PushNotificationService:
    """Push notification service for mobile devices"""
    
    def __init__(self):
        self.fcm_server_key = None  # Would be loaded from config
        self.apns_cert_path = None  # Would be loaded from config
    
    async def send_notification(self, push_token: str, message: UIMessage) -> bool:
        """Send push notification"""
        try:
            # Determine platform from token format
            if push_token.startswith("ios_"):
                return await self._send_apns_notification(push_token, message)
            else:
                return await self._send_fcm_notification(push_token, message)
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    async def _send_fcm_notification(self, token: str, message: UIMessage) -> bool:
        """Send FCM notification"""
        try:
            # This would integrate with Firebase Cloud Messaging
            # For now, we'll just log the notification
            logger.info(f"FCM notification to {token}: {message.response if hasattr(message, 'response') else message.type}")
            return True
        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")
            return False
    
    async def _send_apns_notification(self, token: str, message: UIMessage) -> bool:
        """Send APNS notification"""
        try:
            # This would integrate with Apple Push Notification Service
            # For now, we'll just log the notification
            logger.info(f"APNS notification to {token}: {message.response if hasattr(message, 'response') else message.type}")
            return True
        except Exception as e:
            logger.error(f"Error sending APNS notification: {e}")
            return False
