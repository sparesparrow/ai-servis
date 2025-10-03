"""
AI Communications MCP Server
Provides messaging capabilities via SMS, email, and other communication channels
"""
import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from mcp_framework import MCPServer, MCPMessage, create_tool

from messaging_service_abstraction import (
    MessagingServiceManager, Message, MessageType, MessageStatus, MessagePriority, Contact
)
from message_queue_manager import MessageQueueManager, RetryStrategy
from social_media_services import SocialMediaServiceManager, SocialMediaType, SocialMediaPost

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CommunicationsMCP(MCPServer):
    """AI Communications MCP Server"""
    
    def __init__(self):
        super().__init__("ai-communications", "1.0.0")
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.service_manager = MessagingServiceManager(self.config)
        self.social_media_manager = SocialMediaServiceManager(self.config)
        self.queue_manager = MessageQueueManager(self.config)
        
        # Set up tools
        self._setup_tools()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and config files"""
        config = {
            # Twilio SMS configuration
            "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
            "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
            "twilio_from_number": os.getenv("TWILIO_FROM_NUMBER"),
            "twilio_status_callback": os.getenv("TWILIO_STATUS_CALLBACK"),
            
            # Email configuration
            "smtp_host": os.getenv("SMTP_HOST"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_username": os.getenv("SMTP_USERNAME"),
            "smtp_password": os.getenv("SMTP_PASSWORD"),
            "smtp_use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            
            "imap_host": os.getenv("IMAP_HOST"),
            "imap_port": int(os.getenv("IMAP_PORT", "993")),
            "imap_username": os.getenv("IMAP_USERNAME"),
            "imap_password": os.getenv("IMAP_PASSWORD"),
            "imap_use_ssl": os.getenv("IMAP_USE_SSL", "true").lower() == "true",
            
            # Queue configuration
            "max_queue_size": int(os.getenv("MAX_QUEUE_SIZE", "10000")),
            "default_max_retries": int(os.getenv("DEFAULT_MAX_RETRIES", "3")),
            "default_retry_strategy": os.getenv("DEFAULT_RETRY_STRATEGY", "exponential_backoff"),
            "batch_size": int(os.getenv("BATCH_SIZE", "10")),
            "processing_interval": float(os.getenv("PROCESSING_INTERVAL", "1.0")),
            
            # Social media configuration
            "whatsapp_access_token": os.getenv("WHATSAPP_ACCESS_TOKEN"),
            "whatsapp_phone_number_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
            "whatsapp_business_account_id": os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID"),
            "whatsapp_webhook_verify_token": os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN"),
            
            "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            
            "twitter_bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
            "twitter_api_key": os.getenv("TWITTER_API_KEY"),
            "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
            "twitter_access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
            "twitter_access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            
            "signal_server_url": os.getenv("SIGNAL_SERVER_URL", "http://localhost:8080"),
            "signal_phone_number": os.getenv("SIGNAL_PHONE_NUMBER"),
            "signal_password": os.getenv("SIGNAL_PASSWORD"),
            
            "facebook_page_access_token": os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"),
            "facebook_app_secret": os.getenv("FACEBOOK_APP_SECRET"),
            "facebook_verify_token": os.getenv("FACEBOOK_VERIFY_TOKEN")
        }
        
        # Load from config file if exists
        config_file = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")
        
        return config
    
    def _setup_tools(self):
        """Set up MCP tools"""
        
        # Message sending tools
        self.add_tool(create_tool(
            "send_sms",
            "Send SMS message",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient phone number"},
                    "body": {"type": "string", "description": "Message body"},
                    "priority": {"type": "string", "description": "Message priority (low, normal, high, urgent)"}
                },
                "required": ["to", "body"]
            }
        ))
        
        self.add_tool(create_tool(
            "send_email",
            "Send email message",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"},
                    "attachments": {"type": "array", "description": "List of attachment file paths"},
                    "priority": {"type": "string", "description": "Message priority (low, normal, high, urgent)"}
                },
                "required": ["to", "subject", "body"]
            }
        ))
        
        self.add_tool(create_tool(
            "send_message",
            "Send message via any available service",
            {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (sms, email)"},
                    "to": {"type": "string", "description": "Recipient address"},
                    "subject": {"type": "string", "description": "Message subject (for email)"},
                    "body": {"type": "string", "description": "Message body"},
                    "attachments": {"type": "array", "description": "List of attachment file paths"},
                    "priority": {"type": "string", "description": "Message priority (low, normal, high, urgent)"}
                },
                "required": ["type", "to", "body"]
            }
        ))
        
        # Message receiving tools
        self.add_tool(create_tool(
            "receive_messages",
            "Receive messages from all services",
            {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type to receive (sms, email, all)"},
                    "limit": {"type": "integer", "description": "Maximum number of messages to receive"}
                },
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "get_message_status",
            "Get message delivery status",
            {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Message ID"},
                    "type": {"type": "string", "description": "Message type (sms, email)"}
                },
                "required": ["message_id", "type"]
            }
        ))
        
        # Contact management tools
        self.add_tool(create_tool(
            "get_contacts",
            "Get contacts from messaging services",
            {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Service type to get contacts from (sms, email, all)"}
                },
                "required": []
            }
        ))
        
        # Queue management tools
        self.add_tool(create_tool(
            "get_queue_status",
            "Get message queue status",
            {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type to check queue for (sms, email, all)"}
                },
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "get_queue_statistics",
            "Get message queue statistics",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "clear_queue",
            "Clear messages from queue",
            {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type to clear queue for"}
                },
                "required": ["type"]
            }
        ))
        
        # Service management tools
        self.add_tool(create_tool(
            "authenticate_services",
            "Authenticate with all messaging services",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "get_service_status",
            "Get status of messaging services",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        # Social media tools
        self.add_tool(create_tool(
            "send_whatsapp_message",
            "Send WhatsApp message",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient phone number"},
                    "body": {"type": "string", "description": "Message body"},
                    "media_url": {"type": "string", "description": "Media URL (optional)"}
                },
                "required": ["to", "body"]
            }
        ))
        
        self.add_tool(create_tool(
            "send_telegram_message",
            "Send Telegram message",
            {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "Chat ID or username"},
                    "text": {"type": "string", "description": "Message text"},
                    "parse_mode": {"type": "string", "description": "Parse mode (HTML, Markdown)"}
                },
                "required": ["chat_id", "text"]
            }
        ))
        
        self.add_tool(create_tool(
            "send_twitter_post",
            "Send Twitter/X post",
            {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Tweet text (max 280 characters)"},
                    "reply_to_tweet_id": {"type": "string", "description": "Tweet ID to reply to (optional)"}
                },
                "required": ["text"]
            }
        ))
        
        self.add_tool(create_tool(
            "send_signal_message",
            "Send Signal message",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient phone number"},
                    "message": {"type": "string", "description": "Message text"}
                },
                "required": ["to", "message"]
            }
        ))
        
        self.add_tool(create_tool(
            "send_facebook_message",
            "Send Facebook Messenger message",
            {
                "type": "object",
                "properties": {
                    "recipient_id": {"type": "string", "description": "Recipient Facebook ID"},
                    "text": {"type": "string", "description": "Message text"}
                },
                "required": ["recipient_id", "text"]
            }
        ))
        
        self.add_tool(create_tool(
            "get_social_media_messages",
            "Get messages from social media platforms",
            {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "Platform (whatsapp, telegram, twitter, signal, facebook, all)"},
                    "limit": {"type": "integer", "description": "Maximum number of messages"}
                },
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "get_social_media_contacts",
            "Get contacts from social media platforms",
            {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "Platform (whatsapp, telegram, twitter, signal, facebook, all)"}
                },
                "required": []
            }
        ))
        
        self.add_tool(create_tool(
            "authenticate_social_media",
            "Authenticate with social media services",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
    
    async def start(self):
        """Start the communications server"""
        try:
            logger.info("Starting AI Communications MCP Server")
            
            # Authenticate with services
            auth_results = await self.service_manager.authenticate_all()
            logger.info(f"Service authentication results: {auth_results}")
            
            # Authenticate with social media services
            social_auth_results = await self.social_media_manager.authenticate_all()
            logger.info(f"Social media authentication results: {social_auth_results}")
            
            # Start queue manager
            await self.queue_manager.start()
            
            # Start MCP server
            await super().start()
            
            logger.info("AI Communications MCP Server started")
            
        except Exception as e:
            logger.error(f"Error starting communications server: {e}")
            raise
    
    async def stop(self):
        """Stop the communications server"""
        try:
            logger.info("Stopping AI Communications MCP Server")
            
            # Stop queue manager
            await self.queue_manager.stop()
            
            # Close services
            await self.service_manager.close_all()
            await self.social_media_manager.close_all()
            
            # Stop MCP server
            await super().stop()
            
            logger.info("AI Communications MCP Server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping communications server: {e}")
    
    # Message sending handlers
    async def handle_send_sms(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle sending SMS message"""
        try:
            to = message.params.get("to", "")
            body = message.params.get("body", "")
            priority_str = message.params.get("priority", "normal")
            
            if not to or not body:
                return {"error": "Recipient and message body are required"}
            
            # Create message
            sms_message = Message(
                id=f"sms_{datetime.now().timestamp()}",
                type=MessageType.SMS,
                from_address=self.config.get("twilio_from_number", ""),
                to_address=to,
                body=body,
                priority=MessagePriority(priority_str.lower())
            )
            
            # Send message
            success = await self.service_manager.send_message(sms_message)
            
            if success:
                return {
                    "success": True,
                    "message_id": sms_message.id,
                    "to": to,
                    "status": sms_message.status.value,
                    "message": f"SMS sent to {to}"
                }
            else:
                return {
                    "error": f"Failed to send SMS: {sms_message.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {"error": str(e)}
    
    async def handle_send_email(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle sending email message"""
        try:
            to = message.params.get("to", "")
            subject = message.params.get("subject", "")
            body = message.params.get("body", "")
            attachments = message.params.get("attachments", [])
            priority_str = message.params.get("priority", "normal")
            
            if not to or not subject or not body:
                return {"error": "Recipient, subject, and message body are required"}
            
            # Process attachments
            processed_attachments = []
            for attachment in attachments:
                if os.path.exists(attachment):
                    processed_attachments.append({
                        "path": attachment,
                        "filename": os.path.basename(attachment)
                    })
                else:
                    logger.warning(f"Attachment file not found: {attachment}")
            
            # Create message
            email_message = Message(
                id=f"email_{datetime.now().timestamp()}",
                type=MessageType.EMAIL,
                from_address=self.config.get("smtp_username", ""),
                to_address=to,
                subject=subject,
                body=body,
                attachments=processed_attachments,
                priority=MessagePriority(priority_str.lower())
            )
            
            # Send message
            success = await self.service_manager.send_message(email_message)
            
            if success:
                return {
                    "success": True,
                    "message_id": email_message.id,
                    "to": to,
                    "subject": subject,
                    "status": email_message.status.value,
                    "message": f"Email sent to {to}"
                }
            else:
                return {
                    "error": f"Failed to send email: {email_message.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"error": str(e)}
    
    async def handle_send_message(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle sending message via any service"""
        try:
            message_type_str = message.params.get("type", "").lower()
            to = message.params.get("to", "")
            subject = message.params.get("subject", "")
            body = message.params.get("body", "")
            attachments = message.params.get("attachments", [])
            priority_str = message.params.get("priority", "normal")
            
            if not message_type_str or not to or not body:
                return {"error": "Message type, recipient, and message body are required"}
            
            # Convert message type
            try:
                message_type = MessageType(message_type_str)
            except ValueError:
                return {"error": f"Invalid message type: {message_type_str}"}
            
            # Process attachments for email
            processed_attachments = []
            if message_type == MessageType.EMAIL and attachments:
                for attachment in attachments:
                    if os.path.exists(attachment):
                        processed_attachments.append({
                            "path": attachment,
                            "filename": os.path.basename(attachment)
                        })
                    else:
                        logger.warning(f"Attachment file not found: {attachment}")
            
            # Create message
            msg = Message(
                id=f"{message_type_str}_{datetime.now().timestamp()}",
                type=message_type,
                from_address=self._get_from_address(message_type),
                to_address=to,
                subject=subject if message_type == MessageType.EMAIL else None,
                body=body,
                attachments=processed_attachments,
                priority=MessagePriority(priority_str.lower())
            )
            
            # Send message
            success = await self.service_manager.send_message(msg)
            
            if success:
                return {
                    "success": True,
                    "message_id": msg.id,
                    "type": message_type.value,
                    "to": to,
                    "status": msg.status.value,
                    "message": f"{message_type.value.upper()} sent to {to}"
                }
            else:
                return {
                    "error": f"Failed to send {message_type.value}: {msg.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"error": str(e)}
    
    def _get_from_address(self, message_type: MessageType) -> str:
        """Get from address for message type"""
        if message_type == MessageType.SMS:
            return self.config.get("twilio_from_number", "")
        elif message_type == MessageType.EMAIL:
            return self.config.get("smtp_username", "")
        else:
            return ""
    
    # Message receiving handlers
    async def handle_receive_messages(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle receiving messages"""
        try:
            message_type_str = message.params.get("type", "all")
            limit = message.params.get("limit", 50)
            
            message_type = None
            if message_type_str != "all":
                try:
                    message_type = MessageType(message_type_str.lower())
                except ValueError:
                    return {"error": f"Invalid message type: {message_type_str}"}
            
            # Receive messages
            messages = await self.service_manager.receive_messages(message_type, limit)
            
            # Format response
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg.id,
                    "type": msg.type.value,
                    "from": msg.from_address,
                    "to": msg.to_address,
                    "subject": msg.subject,
                    "body": msg.body,
                    "status": msg.status.value,
                    "created_at": msg.created_at.isoformat(),
                    "sent_at": msg.sent_at.isoformat() if msg.sent_at else None
                })
            
            return {
                "success": True,
                "messages": formatted_messages,
                "count": len(formatted_messages)
            }
            
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            return {"error": str(e)}
    
    async def handle_get_message_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting message status"""
        try:
            message_id = message.params.get("message_id", "")
            message_type_str = message.params.get("type", "")
            
            if not message_id or not message_type_str:
                return {"error": "Message ID and type are required"}
            
            try:
                message_type = MessageType(message_type_str.lower())
            except ValueError:
                return {"error": f"Invalid message type: {message_type_str}"}
            
            # Get message status
            status = await self.service_manager.get_message_status(message_id, message_type)
            
            if status:
                return {
                    "success": True,
                    "message_id": message_id,
                    "type": message_type.value,
                    "status": status.value
                }
            else:
                return {"error": f"Message {message_id} not found"}
                
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return {"error": str(e)}
    
    # Contact management handlers
    async def handle_get_contacts(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting contacts"""
        try:
            message_type_str = message.params.get("type", "all")
            
            message_type = None
            if message_type_str != "all":
                try:
                    message_type = MessageType(message_type_str.lower())
                except ValueError:
                    return {"error": f"Invalid message type: {message_type_str}"}
            
            # Get contacts
            contacts = await self.service_manager.get_contacts(message_type)
            
            # Format response
            formatted_contacts = []
            for contact in contacts:
                formatted_contacts.append({
                    "id": contact.id,
                    "name": contact.name,
                    "phone": contact.phone,
                    "email": contact.email,
                    "addresses": contact.addresses
                })
            
            return {
                "success": True,
                "contacts": formatted_contacts,
                "count": len(formatted_contacts)
            }
            
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return {"error": str(e)}
    
    # Queue management handlers
    async def handle_get_queue_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting queue status"""
        try:
            message_type_str = message.params.get("type", "all")
            
            message_type = None
            if message_type_str != "all":
                try:
                    message_type = MessageType(message_type_str.lower())
                except ValueError:
                    return {"error": f"Invalid message type: {message_type_str}"}
            
            # Get queue status
            status = await self.queue_manager.get_queue_status(message_type)
            
            return {
                "success": True,
                "queue_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {"error": str(e)}
    
    async def handle_get_queue_statistics(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting queue statistics"""
        try:
            statistics = await self.queue_manager.get_statistics()
            
            return {
                "success": True,
                "statistics": statistics
            }
            
        except Exception as e:
            logger.error(f"Error getting queue statistics: {e}")
            return {"error": str(e)}
    
    async def handle_clear_queue(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle clearing queue"""
        try:
            message_type_str = message.params.get("type", "")
            
            if not message_type_str:
                return {"error": "Message type is required"}
            
            try:
                message_type = MessageType(message_type_str.lower())
            except ValueError:
                return {"error": f"Invalid message type: {message_type_str}"}
            
            # Clear queue
            cleared_count = await self.queue_manager.clear_queue(message_type)
            
            return {
                "success": True,
                "message_type": message_type.value,
                "cleared_count": cleared_count,
                "message": f"Cleared {cleared_count} messages from {message_type.value} queue"
            }
            
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")
            return {"error": str(e)}
    
    # Service management handlers
    async def handle_authenticate_services(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle authenticating services"""
        try:
            auth_results = await self.service_manager.authenticate_all()
            
            return {
                "success": True,
                "authentication_results": {k.value: v for k, v in auth_results.items()}
            }
            
        except Exception as e:
            logger.error(f"Error authenticating services: {e}")
            return {"error": str(e)}
    
    async def handle_get_service_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting service status"""
        try:
            status = {}
            for service_type, service in self.service_manager.services.items():
                status[service_type.value] = {
                    "available": True,
                    "authenticated": service.is_authenticated,
                    "service_type": service_type.value
                }
            
            return {
                "success": True,
                "services": status
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {"error": str(e)}
    
    # Social media handlers
    async def handle_send_whatsapp_message(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle sending WhatsApp message"""
        try:
            to = message.params.get("to", "")
            body = message.params.get("body", "")
            media_url = message.params.get("media_url")
            
            if not to or not body:
                return {"error": "Recipient and message body are required"}
            
            # Create message
            whatsapp_message = Message(
                id=f"whatsapp_{datetime.now().timestamp()}",
                type=MessageType.WHATSAPP,
                from_address=self.config.get("whatsapp_phone_number_id", ""),
                to_address=to,
                body=body,
                attachments=[{"url": media_url}] if media_url else []
            )
            
            # Send message
            success = await self.social_media_manager.send_message(whatsapp_message)
            
            if success:
                return {
                    "success": True,
                    "message_id": whatsapp_message.id,
                    "to": to,
                    "status": whatsapp_message.status.value,
                    "message": f"WhatsApp message sent to {to}"
                }
            else:
                return {
                    "error": f"Failed to send WhatsApp message: {whatsapp_message.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {"error": str(e)}
    
    async def handle_send_telegram_message(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle sending Telegram message"""
        try:
            chat_id = message.params.get("chat_id", "")
            text = message.params.get("text", "")
            parse_mode = message.params.get("parse_mode", "HTML")
            
            if not chat_id or not text:
                return {"error": "Chat ID and message text are required"}
            
            # Create message
            telegram_message = Message(
                id=f"telegram_{datetime.now().timestamp()}",
                type=MessageType.TELEGRAM,
                from_address="bot",
                to_address=chat_id,
                body=text,
                metadata={"parse_mode": parse_mode}
            )
            
            # Send message
            success = await self.social_media_manager.send_message(telegram_message)
            
            if success:
                return {
                    "success": True,
                    "message_id": telegram_message.id,
                    "chat_id": chat_id,
                    "status": telegram_message.status.value,
                    "message": f"Telegram message sent to {chat_id}"
                }
            else:
                return {
                    "error": f"Failed to send Telegram message: {telegram_message.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return {"error": str(e)}
    
    async def handle_send_twitter_post(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle sending Twitter post"""
        try:
            text = message.params.get("text", "")
            reply_to_tweet_id = message.params.get("reply_to_tweet_id")
            
            if not text:
                return {"error": "Tweet text is required"}
            
            if len(text) > 280:
                return {"error": "Tweet text exceeds 280 character limit"}
            
            # Create message
            twitter_message = Message(
                id=f"twitter_{datetime.now().timestamp()}",
                type=MessageType.TWITTER,
                from_address="me",
                to_address="public",
                body=text,
                metadata={"reply_to_tweet_id": reply_to_tweet_id} if reply_to_tweet_id else {}
            )
            
            # Send message
            success = await self.social_media_manager.send_message(twitter_message)
            
            if success:
                return {
                    "success": True,
                    "message_id": twitter_message.id,
                    "text": text,
                    "status": twitter_message.status.value,
                    "message": "Twitter post sent successfully"
                }
            else:
                return {
                    "error": f"Failed to send Twitter post: {twitter_message.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error sending Twitter post: {e}")
            return {"error": str(e)}
    
    async def handle_send_signal_message(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle sending Signal message"""
        try:
            to = message.params.get("to", "")
            message_text = message.params.get("message", "")
            
            if not to or not message_text:
                return {"error": "Recipient and message text are required"}
            
            # Create message
            signal_message = Message(
                id=f"signal_{datetime.now().timestamp()}",
                type=MessageType.SIGNAL,
                from_address=self.config.get("signal_phone_number", ""),
                to_address=to,
                body=message_text
            )
            
            # Send message
            success = await self.social_media_manager.send_message(signal_message)
            
            if success:
                return {
                    "success": True,
                    "message_id": signal_message.id,
                    "to": to,
                    "status": signal_message.status.value,
                    "message": f"Signal message sent to {to}"
                }
            else:
                return {
                    "error": f"Failed to send Signal message: {signal_message.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error sending Signal message: {e}")
            return {"error": str(e)}
    
    async def handle_send_facebook_message(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle sending Facebook Messenger message"""
        try:
            recipient_id = message.params.get("recipient_id", "")
            text = message.params.get("text", "")
            
            if not recipient_id or not text:
                return {"error": "Recipient ID and message text are required"}
            
            # Create message
            facebook_message = Message(
                id=f"facebook_{datetime.now().timestamp()}",
                type=MessageType.FACEBOOK,
                from_address="page",
                to_address=recipient_id,
                body=text
            )
            
            # Send message
            success = await self.social_media_manager.send_message(facebook_message)
            
            if success:
                return {
                    "success": True,
                    "message_id": facebook_message.id,
                    "recipient_id": recipient_id,
                    "status": facebook_message.status.value,
                    "message": f"Facebook message sent to {recipient_id}"
                }
            else:
                return {
                    "error": f"Failed to send Facebook message: {facebook_message.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error sending Facebook message: {e}")
            return {"error": str(e)}
    
    async def handle_get_social_media_messages(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting social media messages"""
        try:
            platform = message.params.get("platform", "all")
            limit = message.params.get("limit", 50)
            
            message_type = None
            if platform != "all":
                try:
                    message_type = MessageType(platform.upper())
                except ValueError:
                    return {"error": f"Invalid platform: {platform}"}
            
            # Get messages
            messages = await self.social_media_manager.receive_messages(message_type, limit)
            
            # Format response
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg.id,
                    "platform": msg.type.value,
                    "from": msg.from_address,
                    "to": msg.to_address,
                    "body": msg.body,
                    "status": msg.status.value,
                    "created_at": msg.created_at.isoformat(),
                    "metadata": msg.metadata
                })
            
            return {
                "success": True,
                "messages": formatted_messages,
                "count": len(formatted_messages)
            }
            
        except Exception as e:
            logger.error(f"Error getting social media messages: {e}")
            return {"error": str(e)}
    
    async def handle_get_social_media_contacts(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle getting social media contacts"""
        try:
            platform = message.params.get("platform", "all")
            
            message_type = None
            if platform != "all":
                try:
                    message_type = MessageType(platform.upper())
                except ValueError:
                    return {"error": f"Invalid platform: {platform}"}
            
            # Get contacts
            contacts = await self.social_media_manager.get_contacts(message_type)
            
            # Format response
            formatted_contacts = []
            for contact in contacts:
                formatted_contacts.append({
                    "id": contact.id,
                    "name": contact.name,
                    "phone": contact.phone,
                    "email": contact.email,
                    "addresses": contact.addresses,
                    "metadata": contact.metadata
                })
            
            return {
                "success": True,
                "contacts": formatted_contacts,
                "count": len(formatted_contacts)
            }
            
        except Exception as e:
            logger.error(f"Error getting social media contacts: {e}")
            return {"error": str(e)}
    
    async def handle_authenticate_social_media(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle authenticating social media services"""
        try:
            auth_results = await self.social_media_manager.authenticate_all()
            
            return {
                "success": True,
                "authentication_results": {k.value: v for k, v in auth_results.items()}
            }
            
        except Exception as e:
            logger.error(f"Error authenticating social media services: {e}")
            return {"error": str(e)}


async def main():
    """Main entry point"""
    logger.info("Starting AI Communications MCP Server")
    
    # Create and start communications server
    communications_server = CommunicationsMCP()
    
    try:
        await communications_server.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await communications_server.stop()


if __name__ == "__main__":
    asyncio.run(main())
