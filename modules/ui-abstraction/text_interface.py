"""
Text-based Interface Handler for AI-SERVIS
Handles text input/output via various channels (CLI, IRC, Telegram, etc.)
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from aiohttp import web, web_request
import sys
import os

from ui_models import (
    UIAdapter, UIAdapterConfig, InterfaceType, MessageType,
    CommandMessage, ResponseMessage, StatusMessage, ErrorMessage, UIMessage
)

logger = logging.getLogger(__name__)


class TextInterface(UIAdapter):
    """Text-based interface adapter"""
    
    def __init__(self, config: UIAdapterConfig):
        super().__init__(config)
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.app = None
        self.runner = None
        self.site = None
        self.cli_session = None
    
    async def start(self) -> None:
        """Start text interface server"""
        if not self.config.enabled:
            return
        
        try:
            # Start HTTP server for web-based text interface
            self.app = web.Application()
            self._setup_routes()
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(
                self.runner,
                self.config.host,
                self.config.port or 8082
            )
            await self.site.start()
            
            # Start CLI interface if enabled
            if self.config.custom_settings.get("enable_cli", True):
                asyncio.create_task(self._start_cli_interface())
            
            self.is_running = True
            logger.info(f"Text interface started on {self.config.host}:{self.config.port or 8082}")
            
        except Exception as e:
            logger.error(f"Failed to start text interface: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop text interface server"""
        self.is_running = False
        
        if self.site:
            await self.site.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        # Stop CLI interface
        if self.cli_session:
            self.cli_session.close()
        
        self.connections.clear()
        logger.info("Text interface stopped")
    
    async def send_message(self, message: UIMessage, connection_id: Optional[str] = None) -> bool:
        """Send message to text interface"""
        try:
            if connection_id and connection_id in self.connections:
                connection = self.connections[connection_id]
                connection_type = connection.get("type", "http")
                
                if connection_type == "http":
                    # Send via HTTP response
                    await self._send_http_response(connection_id, message)
                elif connection_type == "cli":
                    # Send via CLI
                    await self._send_cli_response(connection_id, message)
                elif connection_type == "websocket":
                    # Send via WebSocket
                    await self._send_websocket_response(connection_id, message)
                
                self.stats.messages_sent += 1
                return True
            elif not connection_id:
                # Broadcast to all connections
                return await self.broadcast_message(message) > 0
            return False
        except Exception as e:
            logger.error(f"Error sending message to text interface: {e}")
            self.stats.errors += 1
            return False
    
    async def broadcast_message(self, message: UIMessage) -> int:
        """Broadcast message to all text connections"""
        sent_count = 0
        disconnected = []
        
        for connection_id, connection in self.connections.items():
            try:
                connection_type = connection.get("type", "http")
                
                if connection_type == "http":
                    await self._send_http_response(connection_id, message)
                elif connection_type == "cli":
                    await self._send_cli_response(connection_id, message)
                elif connection_type == "websocket":
                    await self._send_websocket_response(connection_id, message)
                
                sent_count += 1
                self.stats.messages_sent += 1
            except Exception as e:
                logger.error(f"Error broadcasting to connection {connection_id}: {e}")
                self.stats.errors += 1
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self._handle_disconnection(connection_id)
        
        return sent_count
    
    def _setup_routes(self) -> None:
        """Setup HTTP routes"""
        self.app.router.add_get("/", self._handle_index)
        self.app.router.add_post("/api/command", self._handle_command)
        self.app.router.add_get("/api/status", self._handle_status)
        self.app.router.add_get("/api/chat", self._handle_chat_interface)
        self.app.router.add_websocket("/ws", self._handle_websocket)
        
        # Add CORS middleware
        self.app.middlewares.append(self._cors_middleware)
    
    async def _cors_middleware(self, request: web_request.Request, handler):
        """CORS middleware"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    async def _handle_index(self, request: web_request.Request) -> web.Response:
        """Handle index page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI-SERVIS Text Interface</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .chat-box { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; margin: 20px 0; }
                .input-box { width: 100%; padding: 10px; margin: 10px 0; }
                .button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
                .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
                .user-message { background: #e3f2fd; text-align: right; }
                .ai-message { background: #f5f5f5; }
                .error-message { background: #ffebee; color: #c62828; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>AI-SERVIS Text Interface</h1>
                <div id="chat-box" class="chat-box"></div>
                <input type="text" id="command-input" class="input-box" placeholder="Enter your command...">
                <button onclick="sendCommand()" class="button">Send</button>
                <button onclick="clearChat()" class="button">Clear</button>
            </div>
            
            <script>
                const chatBox = document.getElementById('chat-box');
                const commandInput = document.getElementById('command-input');
                
                function addMessage(message, type = 'ai-message') {
                    const div = document.createElement('div');
                    div.className = `message ${type}`;
                    div.textContent = message;
                    chatBox.appendChild(div);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
                
                async function sendCommand() {
                    const command = commandInput.value.trim();
                    if (!command) return;
                    
                    addMessage(command, 'user-message');
                    commandInput.value = '';
                    
                    try {
                        const response = await fetch('/api/command', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ command: command })
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            addMessage(result.response, 'ai-message');
                        } else {
                            addMessage(`Error: ${result.error}`, 'error-message');
                        }
                    } catch (error) {
                        addMessage(`Error: ${error.message}`, 'error-message');
                    }
                }
                
                function clearChat() {
                    chatBox.innerHTML = '';
                }
                
                commandInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendCommand();
                    }
                });
                
                // Add welcome message
                addMessage('Welcome to AI-SERVIS! Type your commands below.', 'ai-message');
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_command(self, request: web_request.Request) -> web.Response:
        """Handle command request"""
        try:
            data = await request.json()
            command = data.get("command", "")
            user_id = data.get("user_id", "anonymous")
            session_id = data.get("session_id", str(uuid.uuid4()))
            context = data.get("context", {})
            
            # Create connection ID
            connection_id = str(uuid.uuid4())
            self.connections[connection_id] = {
                "type": "http",
                "request": request,
                "user_id": user_id,
                "session_id": session_id,
                "created_at": datetime.now()
            }
            
            await self.handle_connection(connection_id)
            
            # Create command message
            command_message = CommandMessage(
                id=str(uuid.uuid4()),
                interface_type=InterfaceType.TEXT,
                user_id=user_id,
                session_id=session_id,
                command=command,
                context=context,
                data={"connection_id": connection_id}
            )
            
            # Handle the command
            await self.handle_message(command_message, connection_id)
            
            # Wait for response (in a real implementation, this would be async)
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Return response
            return web.json_response({
                "success": True,
                "response": f"Command processed: {command}",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    async def _handle_status(self, request: web_request.Request) -> web.Response:
        """Handle status request"""
        try:
            stats = self.get_stats()
            return web.json_response({
                "status": "running",
                "stats": stats.dict(),
                "connections": len(self.connections),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error handling status: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_chat_interface(self, request: web_request.Request) -> web.Response:
        """Handle chat interface request"""
        # Redirect to main interface
        return web.HTTPFound("/")
    
    async def _handle_websocket(self, request: web_request.Request) -> web.WebSocketResponse:
        """Handle WebSocket connection"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        connection_id = str(uuid.uuid4())
        self.connections[connection_id] = {
            "type": "websocket",
            "websocket": ws,
            "user_id": "anonymous",
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now()
        }
        
        await self.handle_connection(connection_id)
        
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
            await self._handle_disconnection(connection_id)
        
        return ws
    
    async def _handle_websocket_message(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle WebSocket message"""
        try:
            message_type = data.get("type")
            
            if message_type == "command":
                command = data.get("command", "")
                user_id = data.get("user_id", "anonymous")
                session_id = data.get("session_id", str(uuid.uuid4()))
                context = data.get("context", {})
                
                # Create command message
                command_message = CommandMessage(
                    id=str(uuid.uuid4()),
                    interface_type=InterfaceType.TEXT,
                    user_id=user_id,
                    session_id=session_id,
                    command=command,
                    context=context,
                    data={"connection_id": connection_id}
                )
                
                # Handle the command
                await self.handle_message(command_message, connection_id)
                
            elif message_type == "heartbeat":
                # Handle heartbeat
                heartbeat_message = UIMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.HEARTBEAT,
                    interface_type=InterfaceType.TEXT,
                    user_id=data.get("user_id"),
                    session_id=data.get("session_id"),
                    data={"connection_id": connection_id}
                )
                
                await self.handle_message(heartbeat_message, connection_id)
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            self.stats.errors += 1
    
    async def _start_cli_interface(self) -> None:
        """Start CLI interface"""
        try:
            # Create CLI session
            self.cli_session = CLISession(self)
            await self.cli_session.start()
        except Exception as e:
            logger.error(f"Error starting CLI interface: {e}")
    
    async def _send_http_response(self, connection_id: str, message: UIMessage) -> None:
        """Send HTTP response"""
        # In a real implementation, this would send the response back to the HTTP client
        # For now, we'll just log it
        logger.info(f"HTTP response for {connection_id}: {message.response if hasattr(message, 'response') else message.type}")
    
    async def _send_cli_response(self, connection_id: str, message: UIMessage) -> None:
        """Send CLI response"""
        if self.cli_session:
            await self.cli_session.send_response(message)
    
    async def _send_websocket_response(self, connection_id: str, message: UIMessage) -> None:
        """Send WebSocket response"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            if connection.get("type") == "websocket":
                ws = connection.get("websocket")
                if ws:
                    try:
                        await ws.send_str(json.dumps(message.dict()))
                    except Exception as e:
                        logger.error(f"Error sending WebSocket response: {e}")
    
    async def _handle_disconnection(self, connection_id: str) -> None:
        """Handle connection disconnection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        await self.handle_disconnection(connection_id)


class CLISession:
    """CLI session handler"""
    
    def __init__(self, text_interface: TextInterface):
        self.text_interface = text_interface
        self.connection_id = str(uuid.uuid4())
        self.is_running = False
    
    async def start(self) -> None:
        """Start CLI session"""
        self.is_running = True
        
        # Register connection
        self.text_interface.connections[self.connection_id] = {
            "type": "cli",
            "session": self,
            "user_id": "cli_user",
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now()
        }
        
        await self.text_interface.handle_connection(self.connection_id)
        
        print("AI-SERVIS CLI Interface")
        print("Type 'exit' to quit, 'help' for commands")
        print("-" * 40)
        
        try:
            while self.is_running:
                try:
                    # Read input from stdin
                    command = await asyncio.get_event_loop().run_in_executor(
                        None, input, "AI-SERVIS> "
                    )
                    
                    if command.lower() in ['exit', 'quit']:
                        break
                    
                    if command.lower() == 'help':
                        self._show_help()
                        continue
                    
                    if command.strip():
                        # Create command message
                        command_message = CommandMessage(
                            id=str(uuid.uuid4()),
                            interface_type=InterfaceType.TEXT,
                            user_id="cli_user",
                            session_id=self.text_interface.connections[self.connection_id]["session_id"],
                            command=command,
                            data={"connection_id": self.connection_id}
                        )
                        
                        # Handle the command
                        await self.text_interface.handle_message(command_message, self.connection_id)
                
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
        finally:
            await self.text_interface._handle_disconnection(self.connection_id)
            print("\nGoodbye!")
    
    def _show_help(self) -> None:
        """Show help information"""
        help_text = """
Available commands:
- play music [artist/song] - Play music
- volume [up/down/number] - Control volume
- lights [on/off/dim] - Control lights
- weather - Get weather information
- time - Get current time
- help - Show this help
- exit/quit - Exit CLI
        """
        print(help_text)
    
    async def send_response(self, message: UIMessage) -> None:
        """Send response to CLI"""
        if hasattr(message, 'response'):
            print(f"AI: {message.response}")
        elif hasattr(message, 'error_message'):
            print(f"Error: {message.error_message}")
        elif hasattr(message, 'status'):
            print(f"Status: {message.status}")
        else:
            print(f"Message: {message.type}")
    
    def close(self) -> None:
        """Close CLI session"""
        self.is_running = False
