"""
Web Interface Adapter for AI-SERVIS
Provides web-based UI with modern interface and real-time communication
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from aiohttp import web, web_request
import socketio
from pathlib import Path

from ui_models import (
    UIAdapter, UIAdapterConfig, InterfaceType, MessageType,
    CommandMessage, ResponseMessage, StatusMessage, ErrorMessage, 
    NotificationMessage, UIMessage
)

logger = logging.getLogger(__name__)


class WebInterface(UIAdapter):
    """Web interface adapter with Socket.IO support"""
    
    def __init__(self, config: UIAdapterConfig):
        super().__init__(config)
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.app = None
        self.sio = None
        self.runner = None
        self.site = None
        self.static_dir = Path(__file__).parent / "static"
        self.static_dir.mkdir(exist_ok=True)
    
    async def start(self) -> None:
        """Start web interface server"""
        if not self.config.enabled:
            return
        
        try:
            # Create Socket.IO server
            self.sio = socketio.AsyncServer(
                cors_allowed_origins="*",
                logger=True,
                engineio_logger=True
            )
            
            # Create aiohttp app
            self.app = web.Application()
            self.sio.attach(self.app)
            
            # Setup routes
            self._setup_routes()
            
            # Setup Socket.IO events
            self._setup_socketio_events()
            
            # Create static files
            await self._create_static_files()
            
            # Start server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(
                self.runner,
                self.config.host,
                self.config.port or 8083
            )
            await self.site.start()
            
            self.is_running = True
            logger.info(f"Web interface started on {self.config.host}:{self.config.port or 8083}")
            
        except Exception as e:
            logger.error(f"Failed to start web interface: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop web interface server"""
        self.is_running = False
        
        if self.site:
            await self.site.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        self.connections.clear()
        logger.info("Web interface stopped")
    
    async def send_message(self, message: UIMessage, connection_id: Optional[str] = None) -> bool:
        """Send message to web interface"""
        try:
            if connection_id and connection_id in self.connections:
                # Send via Socket.IO
                await self.sio.emit('message', message.dict(), room=connection_id)
                self.stats.messages_sent += 1
                return True
            elif not connection_id:
                # Broadcast to all connections
                return await self.broadcast_message(message) > 0
            return False
        except Exception as e:
            logger.error(f"Error sending message to web interface: {e}")
            self.stats.errors += 1
            return False
    
    async def broadcast_message(self, message: UIMessage) -> int:
        """Broadcast message to all web connections"""
        try:
            await self.sio.emit('message', message.dict())
            self.stats.messages_sent += len(self.connections)
            return len(self.connections)
        except Exception as e:
            logger.error(f"Error broadcasting to web interface: {e}")
            self.stats.errors += 1
            return 0
    
    def _setup_routes(self) -> None:
        """Setup HTTP routes"""
        # Serve static files
        self.app.router.add_static('/', self.static_dir, name='static')
        
        # API routes
        self.app.router.add_get('/api/status', self._handle_status)
        self.app.router.add_get('/api/connections', self._handle_connections)
        self.app.router.add_post('/api/command', self._handle_command)
        
        # Add CORS middleware
        self.app.middlewares.append(self._cors_middleware)
    
    async def _cors_middleware(self, request: web_request.Request, handler):
        """CORS middleware"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
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
    
    async def _handle_connections(self, request: web_request.Request) -> web.Response:
        """Handle connections request"""
        try:
            connections_info = []
            for conn_id, conn_data in self.connections.items():
                connections_info.append({
                    "id": conn_id,
                    "user_id": conn_data.get("user_id"),
                    "session_id": conn_data.get("session_id"),
                    "connected_at": conn_data.get("connected_at", "").isoformat() if conn_data.get("connected_at") else None,
                    "last_activity": conn_data.get("last_activity", "").isoformat() if conn_data.get("last_activity") else None
                })
            
            return web.json_response({
                "connections": connections_info,
                "total": len(connections_info)
            })
        except Exception as e:
            logger.error(f"Error handling connections: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def _handle_command(self, request: web_request.Request) -> web.Response:
        """Handle command request"""
        try:
            data = await request.json()
            command = data.get("command", "")
            user_id = data.get("user_id", "anonymous")
            session_id = data.get("session_id", str(uuid.uuid4()))
            context = data.get("context", {})
            
            # Create command message
            command_message = CommandMessage(
                id=str(uuid.uuid4()),
                interface_type=InterfaceType.WEB,
                user_id=user_id,
                session_id=session_id,
                command=command,
                context=context
            )
            
            # Handle the command
            await self.handle_message(command_message)
            
            return web.json_response({
                "success": True,
                "message_id": command_message.id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    def _setup_socketio_events(self) -> None:
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            connection_id = str(uuid.uuid4())
            self.connections[connection_id] = {
                "sid": sid,
                "user_id": "anonymous",
                "session_id": str(uuid.uuid4()),
                "connected_at": datetime.now(),
                "last_activity": datetime.now()
            }
            
            # Join room for this connection
            await self.sio.enter_room(sid, connection_id)
            
            await self.handle_connection(connection_id)
            
            # Send welcome message
            welcome_message = NotificationMessage(
                id=str(uuid.uuid4()),
                interface_type=InterfaceType.WEB,
                title="Welcome",
                message="Connected to AI-SERVIS Web Interface",
                level="info"
            )
            
            await self.sio.emit('message', welcome_message.dict(), room=sid)
            
            logger.info(f"Web client connected: {connection_id}")
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            # Find connection by sid
            connection_id = None
            for conn_id, conn_data in self.connections.items():
                if conn_data.get("sid") == sid:
                    connection_id = conn_id
                    break
            
            if connection_id:
                await self._handle_disconnection(connection_id)
                logger.info(f"Web client disconnected: {connection_id}")
        
        @self.sio.event
        async def command(sid, data):
            """Handle command from client"""
            try:
                # Find connection by sid
                connection_id = None
                for conn_id, conn_data in self.connections.items():
                    if conn_data.get("sid") == sid:
                        connection_id = conn_id
                        break
                
                if not connection_id:
                    await self.sio.emit('error', {"message": "Connection not found"}, room=sid)
                    return
                
                # Update last activity
                self.connections[connection_id]["last_activity"] = datetime.now()
                
                command_text = data.get("command", "")
                user_id = data.get("user_id", "anonymous")
                session_id = data.get("session_id", self.connections[connection_id]["session_id"])
                context = data.get("context", {})
                
                # Update connection info
                self.connections[connection_id]["user_id"] = user_id
                self.connections[connection_id]["session_id"] = session_id
                
                # Create command message
                command_message = CommandMessage(
                    id=str(uuid.uuid4()),
                    interface_type=InterfaceType.WEB,
                    user_id=user_id,
                    session_id=session_id,
                    command=command_text,
                    context=context,
                    data={"connection_id": connection_id}
                )
                
                # Send status update
                status_message = StatusMessage(
                    id=str(uuid.uuid4()),
                    interface_type=InterfaceType.WEB,
                    user_id=user_id,
                    session_id=session_id,
                    status="Processing command...",
                    data={"connection_id": connection_id}
                )
                
                await self.sio.emit('message', status_message.dict(), room=sid)
                
                # Handle the command
                await self.handle_message(command_message, connection_id)
                
            except Exception as e:
                logger.error(f"Error handling command from {sid}: {e}")
                await self.sio.emit('error', {"message": str(e)}, room=sid)
        
        @self.sio.event
        async def heartbeat(sid, data):
            """Handle heartbeat from client"""
            try:
                # Find connection by sid
                for conn_id, conn_data in self.connections.items():
                    if conn_data.get("sid") == sid:
                        conn_data["last_activity"] = datetime.now()
                        
                        # Create heartbeat message
                        heartbeat_message = UIMessage(
                            id=str(uuid.uuid4()),
                            type=MessageType.HEARTBEAT,
                            interface_type=InterfaceType.WEB,
                            user_id=conn_data.get("user_id"),
                            session_id=conn_data.get("session_id"),
                            data={"connection_id": conn_id}
                        )
                        
                        await self.handle_message(heartbeat_message, conn_id)
                        break
                        
            except Exception as e:
                logger.error(f"Error handling heartbeat from {sid}: {e}")
        
        @self.sio.event
        async def join_room(sid, data):
            """Handle client joining a room"""
            room = data.get("room")
            if room:
                await self.sio.enter_room(sid, room)
                await self.sio.emit('joined_room', {"room": room}, room=sid)
        
        @self.sio.event
        async def leave_room(sid, data):
            """Handle client leaving a room"""
            room = data.get("room")
            if room:
                await self.sio.leave_room(sid, room)
                await self.sio.emit('left_room', {"room": room}, room=sid)
    
    async def _create_static_files(self) -> None:
        """Create static files for web interface"""
        
        # Create main HTML file
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-SERVIS Web Interface</title>
    <script src="/socket.io/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 90%;
            max-width: 800px;
            height: 600px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .status {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            background: #f9f9f9;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .ai-message {
            background: white;
            border: 1px solid #e0e0e0;
            margin-right: auto;
        }
        
        .error-message {
            background: #ffebee;
            border: 1px solid #f44336;
            color: #c62828;
        }
        
        .status-message {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            color: #1565c0;
            text-align: center;
            margin: 0 auto;
        }
        
        .notification-message {
            background: #f3e5f5;
            border: 1px solid #9c27b0;
            color: #6a1b9a;
            text-align: center;
            margin: 0 auto;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        .command-input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .command-input:focus {
            border-color: #667eea;
        }
        
        .send-button {
            padding: 15px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }
        
        .send-button:hover {
            transform: translateY(-2px);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }
        
        .suggestion {
            padding: 8px 15px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        
        .suggestion:hover {
            background: #e0e0e0;
        }
        
        .connection-info {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255,255,255,0.9);
            padding: 10px;
            border-radius: 10px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI-SERVIS Web Interface</h1>
            <div class="status">
                <div class="status-dot" id="status-dot"></div>
                <span id="status-text">Connecting...</span>
            </div>
        </div>
        
        <div class="connection-info">
            <div>Connections: <span id="connection-count">0</span></div>
            <div>User: <span id="user-id">anonymous</span></div>
        </div>
        
        <div class="chat-container">
            <div class="chat-messages" id="chat-messages">
                <div class="message notification-message">
                    Welcome to AI-SERVIS! Type your commands below or use the suggestions.
                </div>
            </div>
            
            <div class="input-container">
                <input type="text" id="command-input" class="command-input" 
                       placeholder="Enter your command..." autocomplete="off">
                <button id="send-button" class="send-button">Send</button>
            </div>
            
            <div class="suggestions" id="suggestions">
                <div class="suggestion" onclick="sendSuggestion('play music')">Play Music</div>
                <div class="suggestion" onclick="sendSuggestion('turn on lights')">Turn On Lights</div>
                <div class="suggestion" onclick="sendSuggestion('what is the weather')">Weather</div>
                <div class="suggestion" onclick="sendSuggestion('set volume to 50')">Volume Control</div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        const chatMessages = document.getElementById('chat-messages');
        const commandInput = document.getElementById('command-input');
        const sendButton = document.getElementById('send-button');
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        const connectionCount = document.getElementById('connection-count');
        const userId = document.getElementById('user-id');
        const suggestions = document.getElementById('suggestions');
        
        let isConnected = false;
        let currentUserId = 'anonymous';
        let currentSessionId = null;
        
        // Socket.IO event handlers
        socket.on('connect', function() {
            isConnected = true;
            statusDot.style.background = '#4CAF50';
            statusText.textContent = 'Connected';
            console.log('Connected to server');
        });
        
        socket.on('disconnect', function() {
            isConnected = false;
            statusDot.style.background = '#f44336';
            statusText.textContent = 'Disconnected';
            console.log('Disconnected from server');
        });
        
        socket.on('message', function(data) {
            handleMessage(data);
        });
        
        socket.on('error', function(data) {
            addMessage('Error: ' + data.message, 'error-message');
        });
        
        socket.on('joined_room', function(data) {
            console.log('Joined room:', data.room);
        });
        
        socket.on('left_room', function(data) {
            console.log('Left room:', data.room);
        });
        
        // Message handling
        function handleMessage(data) {
            switch(data.type) {
                case 'response':
                    addMessage(data.response, 'ai-message');
                    if (data.suggestions && data.suggestions.length > 0) {
                        showSuggestions(data.suggestions);
                    }
                    break;
                case 'status':
                    addMessage(data.status, 'status-message');
                    break;
                case 'error':
                    addMessage(data.error_message, 'error-message');
                    break;
                case 'notification':
                    addMessage(data.title + ': ' + data.message, 'notification-message');
                    break;
                default:
                    addMessage(JSON.stringify(data), 'ai-message');
            }
        }
        
        function addMessage(text, className) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${className}`;
            messageDiv.textContent = text;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function showSuggestions(suggestionList) {
            suggestions.innerHTML = '';
            suggestionList.forEach(suggestion => {
                const suggestionDiv = document.createElement('div');
                suggestionDiv.className = 'suggestion';
                suggestionDiv.textContent = suggestion;
                suggestionDiv.onclick = () => sendSuggestion(suggestion);
                suggestions.appendChild(suggestionDiv);
            });
        }
        
        function sendSuggestion(suggestion) {
            commandInput.value = suggestion;
            sendCommand();
        }
        
        function sendCommand() {
            const command = commandInput.value.trim();
            if (!command || !isConnected) return;
            
            // Add user message to chat
            addMessage(command, 'user-message');
            
            // Send command to server
            socket.emit('command', {
                command: command,
                user_id: currentUserId,
                session_id: currentSessionId,
                context: {}
            });
            
            // Clear input
            commandInput.value = '';
            
            // Disable send button temporarily
            sendButton.disabled = true;
            setTimeout(() => {
                sendButton.disabled = false;
            }, 1000);
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendCommand);
        
        commandInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
        
        // Update connection info periodically
        setInterval(async () => {
            try {
                const response = await fetch('/api/connections');
                const data = await response.json();
                connectionCount.textContent = data.total;
            } catch (error) {
                console.error('Error fetching connection info:', error);
            }
        }, 5000);
        
        // Generate session ID
        currentSessionId = 'session_' + Math.random().toString(36).substr(2, 9);
        
        // Set user ID from localStorage or generate new one
        currentUserId = localStorage.getItem('ai-servis-user-id') || 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('ai-servis-user-id', currentUserId);
        userId.textContent = currentUserId;
    </script>
</body>
</html>
        """
        
        # Write HTML file
        html_file = self.static_dir / "index.html"
        html_file.write_text(html_content)
        
        logger.info(f"Created static files in {self.static_dir}")
    
    async def _handle_disconnection(self, connection_id: str) -> None:
        """Handle connection disconnection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        await self.handle_disconnection(connection_id)
