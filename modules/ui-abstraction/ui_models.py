"""
UI Abstraction Models and Interfaces
"""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from pydantic import BaseModel, Field
import asyncio


class InterfaceType(str, Enum):
    """Supported interface types"""
    VOICE = "voice"
    TEXT = "text"
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    WEBSOCKET = "websocket"


class MessageType(str, Enum):
    """Message types for UI communication"""
    COMMAND = "command"
    RESPONSE = "response"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    NOTIFICATION = "notification"


class UIMessage(BaseModel):
    """Base UI message model"""
    id: str = Field(..., description="Unique message ID")
    type: MessageType = Field(..., description="Message type")
    interface_type: InterfaceType = Field(..., description="Interface type")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CommandMessage(UIMessage):
    """Command message from UI to orchestrator"""
    type: MessageType = MessageType.COMMAND
    command: str = Field(..., description="Command text")
    context: Dict[str, Any] = Field(default_factory=dict, description="Command context")
    priority: int = Field(default=0, description="Command priority (higher = more important)")


class ResponseMessage(UIMessage):
    """Response message from orchestrator to UI"""
    type: MessageType = MessageType.RESPONSE
    response: str = Field(..., description="Response text")
    success: bool = Field(default=True, description="Whether command was successful")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up commands")


class StatusMessage(UIMessage):
    """Status message for UI updates"""
    type: MessageType = MessageType.STATUS
    status: str = Field(..., description="Status text")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Status details")


class ErrorMessage(UIMessage):
    """Error message for UI"""
    type: MessageType = MessageType.ERROR
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Error details")


class NotificationMessage(UIMessage):
    """Notification message for UI"""
    type: MessageType = MessageType.NOTIFICATION
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    level: str = Field(default="info", description="Notification level (info, warning, error)")
    actions: List[Dict[str, str]] = Field(default_factory=list, description="Available actions")


class UIAdapterConfig(BaseModel):
    """Configuration for UI adapters"""
    interface_type: InterfaceType
    enabled: bool = True
    port: Optional[int] = None
    host: str = "localhost"
    max_connections: int = 100
    timeout: int = 30
    authentication_required: bool = False
    ssl_enabled: bool = False
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class UIAdapterStats(BaseModel):
    """Statistics for UI adapter"""
    interface_type: InterfaceType
    active_connections: int = 0
    total_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    uptime: float = 0.0
    last_activity: Optional[datetime] = None


class UIAdapter(ABC):
    """Abstract base class for UI adapters"""
    
    def __init__(self, config: UIAdapterConfig):
        self.config = config
        self.stats = UIAdapterStats(interface_type=config.interface_type)
        self.start_time = datetime.now()
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.connection_handlers: List[Callable] = []
        self.disconnection_handlers: List[Callable] = []
        self.is_running = False
    
    @abstractmethod
    async def start(self) -> None:
        """Start the UI adapter"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the UI adapter"""
        pass
    
    @abstractmethod
    async def send_message(self, message: UIMessage, connection_id: Optional[str] = None) -> bool:
        """Send message to UI"""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message: UIMessage) -> int:
        """Broadcast message to all connected UIs"""
        pass
    
    def add_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Add message handler for specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def add_connection_handler(self, handler: Callable) -> None:
        """Add connection handler"""
        self.connection_handlers.append(handler)
    
    def add_disconnection_handler(self, handler: Callable) -> None:
        """Add disconnection handler"""
        self.disconnection_handlers.append(handler)
    
    async def handle_message(self, message: UIMessage, connection_id: Optional[str] = None) -> None:
        """Handle incoming message"""
        self.stats.messages_received += 1
        self.stats.last_activity = datetime.now()
        
        # Call registered handlers
        handlers = self.message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                await handler(message, connection_id)
            except Exception as e:
                self.stats.errors += 1
                print(f"Error in message handler: {e}")
    
    async def handle_connection(self, connection_id: str) -> None:
        """Handle new connection"""
        self.stats.active_connections += 1
        self.stats.total_connections += 1
        self.stats.last_activity = datetime.now()
        
        # Call registered handlers
        for handler in self.connection_handlers:
            try:
                await handler(connection_id)
            except Exception as e:
                self.stats.errors += 1
                print(f"Error in connection handler: {e}")
    
    async def handle_disconnection(self, connection_id: str) -> None:
        """Handle connection disconnection"""
        self.stats.active_connections = max(0, self.stats.active_connections - 1)
        self.stats.last_activity = datetime.now()
        
        # Call registered handlers
        for handler in self.disconnection_handlers:
            try:
                await handler(connection_id)
            except Exception as e:
                self.stats.errors += 1
                print(f"Error in disconnection handler: {e}")
    
    def get_stats(self) -> UIAdapterStats:
        """Get adapter statistics"""
        self.stats.uptime = (datetime.now() - self.start_time).total_seconds()
        return self.stats


class UIManager:
    """Manager for multiple UI adapters"""
    
    def __init__(self):
        self.adapters: Dict[InterfaceType, UIAdapter] = {}
        self.orchestrator_client = None
        self.message_queue = asyncio.Queue()
        self.is_running = False
    
    def register_adapter(self, adapter: UIAdapter) -> None:
        """Register a UI adapter"""
        self.adapters[adapter.config.interface_type] = adapter
        
        # Set up message forwarding
        adapter.add_message_handler(MessageType.COMMAND, self._forward_to_orchestrator)
        adapter.add_message_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    async def start_all(self) -> None:
        """Start all registered adapters"""
        self.is_running = True
        
        # Start all adapters
        for adapter in self.adapters.values():
            if adapter.config.enabled:
                await adapter.start()
        
        # Start message processing
        asyncio.create_task(self._process_messages())
    
    async def stop_all(self) -> None:
        """Stop all registered adapters"""
        self.is_running = False
        
        for adapter in self.adapters.values():
            await adapter.stop()
    
    async def send_to_interface(self, interface_type: InterfaceType, message: UIMessage) -> bool:
        """Send message to specific interface type"""
        adapter = self.adapters.get(interface_type)
        if adapter:
            return await adapter.send_message(message)
        return False
    
    async def broadcast_to_all(self, message: UIMessage) -> int:
        """Broadcast message to all interfaces"""
        total_sent = 0
        for adapter in self.adapters.values():
            sent = await adapter.broadcast_message(message)
            total_sent += sent
        return total_sent
    
    async def _forward_to_orchestrator(self, message: UIMessage, connection_id: Optional[str] = None) -> None:
        """Forward command message to orchestrator"""
        if self.orchestrator_client:
            try:
                # Convert UI message to orchestrator format
                command_data = {
                    "text": message.data.get("command", ""),
                    "session_id": message.session_id,
                    "user_id": message.user_id,
                    "interface_type": message.interface_type.value,
                    "context": message.data.get("context", {})
                }
                
                # Send to orchestrator
                response = await self.orchestrator_client.call_tool("process_voice_command", command_data)
                
                # Create response message
                response_message = ResponseMessage(
                    id=f"resp_{message.id}",
                    interface_type=message.interface_type,
                    user_id=message.user_id,
                    session_id=message.session_id,
                    response=response.get("response", "Command processed"),
                    success=response.get("success", True),
                    data=response.get("data", {}),
                    suggestions=response.get("suggestions", [])
                )
                
                # Send response back to UI
                await self.send_to_interface(message.interface_type, response_message)
                
            except Exception as e:
                # Send error response
                error_message = ErrorMessage(
                    id=f"err_{message.id}",
                    interface_type=message.interface_type,
                    user_id=message.user_id,
                    session_id=message.session_id,
                    error_code="ORCHESTRATOR_ERROR",
                    error_message=str(e)
                )
                await self.send_to_interface(message.interface_type, error_message)
    
    async def _handle_heartbeat(self, message: UIMessage, connection_id: Optional[str] = None) -> None:
        """Handle heartbeat message"""
        # Update last activity
        adapter = self.adapters.get(message.interface_type)
        if adapter:
            adapter.stats.last_activity = datetime.now()
    
    async def _process_messages(self) -> None:
        """Process messages from queue"""
        while self.is_running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                # Process message here if needed
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing message: {e}")
    
    def get_all_stats(self) -> Dict[InterfaceType, UIAdapterStats]:
        """Get statistics for all adapters"""
        return {interface_type: adapter.get_stats() for interface_type, adapter in self.adapters.items()}
