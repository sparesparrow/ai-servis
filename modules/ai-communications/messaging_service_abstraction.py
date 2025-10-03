"""
Messaging Service Abstraction Layer
Provides unified interface for multiple messaging services
"""
import asyncio
import logging
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import aiohttp
import aiofiles

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types"""
    SMS = "sms"
    MMS = "mms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    TWITTER = "twitter"
    SIGNAL = "signal"
    FACEBOOK = "facebook"


class MessageStatus(Enum):
    """Message status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessagePriority(Enum):
    """Message priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Message:
    """Message representation"""
    id: str
    type: MessageType
    from_address: str
    to_address: str
    subject: Optional[str] = None
    body: str = ""
    attachments: List[Dict[str, Any]] = None
    status: MessageStatus = MessageStatus.PENDING
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MessageThread:
    """Message thread/conversation"""
    id: str
    participants: List[str]
    message_type: MessageType
    subject: Optional[str] = None
    last_message: Optional[Message] = None
    message_count: int = 0
    unread_count: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class Contact:
    """Contact information"""
    id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    addresses: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.addresses is None:
            self.addresses = []
        if self.metadata is None:
            self.metadata = {}


class MessagingService(ABC):
    """Abstract base class for messaging services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_type = self._get_service_type()
        self.is_authenticated = False
        self.session: Optional[aiohttp.ClientSession] = None
    
    @abstractmethod
    def _get_service_type(self) -> MessageType:
        """Get the service type"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass
    
    @abstractmethod
    async def send_message(self, message: Message) -> bool:
        """Send a message"""
        pass
    
    @abstractmethod
    async def receive_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Receive messages"""
        pass
    
    @abstractmethod
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get message delivery status"""
        pass
    
    @abstractmethod
    async def get_contacts(self) -> List[Contact]:
        """Get contacts"""
        pass
    
    async def close(self):
        """Close the service session"""
        if self.session:
            await self.session.close()


class SMSService(MessagingService):
    """SMS messaging service using Twilio"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_sid = config.get("twilio_account_sid")
        self.auth_token = config.get("twilio_auth_token")
        self.from_number = config.get("twilio_from_number")
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
    
    def _get_service_type(self) -> MessageType:
        return MessageType.SMS
    
    async def authenticate(self) -> bool:
        """Authenticate with Twilio"""
        try:
            if not all([self.account_sid, self.auth_token, self.from_number]):
                logger.error("Twilio credentials not configured")
                return False
            
            # Create session with basic auth
            auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
            self.session = aiohttp.ClientSession(auth=auth)
            
            # Test authentication by getting account info
            async with self.session.get(f"{self.base_url}.json") as response:
                if response.status == 200:
                    self.is_authenticated = True
                    logger.info("Twilio SMS authentication successful")
                    return True
                else:
                    logger.error(f"Twilio authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with Twilio: {e}")
            return False
    
    async def send_message(self, message: Message) -> bool:
        """Send SMS message via Twilio"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            if message.type != MessageType.SMS:
                logger.error("Message type must be SMS")
                return False
            
            # Prepare Twilio API request
            data = {
                "From": self.from_number,
                "To": message.to_address,
                "Body": message.body
            }
            
            # Add status callback if configured
            status_callback = self.config.get("twilio_status_callback")
            if status_callback:
                data["StatusCallback"] = status_callback
            
            async with self.session.post(f"{self.base_url}/Messages.json", data=data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    message.id = result["sid"]
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.now()
                    logger.info(f"SMS sent successfully: {message.id}")
                    return True
                else:
                    error_text = await response.text()
                    message.status = MessageStatus.FAILED
                    message.error_message = f"Twilio error: {response.status} - {error_text}"
                    logger.error(f"Failed to send SMS: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            return False
    
    async def receive_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Receive SMS messages from Twilio"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            params = {
                "PageSize": min(limit, 1000),  # Twilio max
                "Page": (offset // limit) + 1
            }
            
            async with self.session.get(f"{self.base_url}/Messages.json", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    messages = []
                    
                    for msg_data in data.get("messages", []):
                        message = Message(
                            id=msg_data["sid"],
                            type=MessageType.SMS,
                            from_address=msg_data["from"],
                            to_address=msg_data["to"],
                            body=msg_data["body"],
                            status=self._parse_twilio_status(msg_data["status"]),
                            created_at=datetime.fromisoformat(msg_data["date_created"].replace("Z", "+00:00")),
                            sent_at=datetime.fromisoformat(msg_data["date_sent"].replace("Z", "+00:00")) if msg_data.get("date_sent") else None,
                            metadata={
                                "direction": msg_data["direction"],
                                "price": msg_data.get("price"),
                                "price_unit": msg_data.get("price_unit")
                            }
                        )
                        messages.append(message)
                    
                    return messages
                else:
                    logger.error(f"Failed to receive SMS messages: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error receiving SMS messages: {e}")
            return []
    
    def _parse_twilio_status(self, status: str) -> MessageStatus:
        """Parse Twilio status to MessageStatus"""
        status_map = {
            "queued": MessageStatus.PENDING,
            "sending": MessageStatus.PENDING,
            "sent": MessageStatus.SENT,
            "delivered": MessageStatus.DELIVERED,
            "undelivered": MessageStatus.FAILED,
            "failed": MessageStatus.FAILED
        }
        return status_map.get(status, MessageStatus.PENDING)
    
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get SMS message status from Twilio"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            async with self.session.get(f"{self.base_url}/Messages/{message_id}.json") as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_twilio_status(data["status"])
                else:
                    logger.error(f"Failed to get SMS status: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting SMS status: {e}")
            return None
    
    async def get_contacts(self) -> List[Contact]:
        """Get contacts (not supported by Twilio SMS)"""
        logger.warning("Contacts not supported by Twilio SMS service")
        return []


class EmailService(MessagingService):
    """Email messaging service using SMTP/IMAP"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_host = config.get("smtp_host")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_username = config.get("smtp_username")
        self.smtp_password = config.get("smtp_password")
        self.smtp_use_tls = config.get("smtp_use_tls", True)
        
        self.imap_host = config.get("imap_host")
        self.imap_port = config.get("imap_port", 993)
        self.imap_username = config.get("imap_username")
        self.imap_password = config.get("imap_password")
        self.imap_use_ssl = config.get("imap_use_ssl", True)
    
    def _get_service_type(self) -> MessageType:
        return MessageType.EMAIL
    
    async def authenticate(self) -> bool:
        """Authenticate with email service"""
        try:
            # Test SMTP connection
            if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
                logger.error("SMTP credentials not configured")
                return False
            
            # Test IMAP connection
            if not all([self.imap_host, self.imap_username, self.imap_password]):
                logger.error("IMAP credentials not configured")
                return False
            
            self.is_authenticated = True
            logger.info("Email service authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating email service: {e}")
            return False
    
    async def send_message(self, message: Message) -> bool:
        """Send email message via SMTP"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            if message.type != MessageType.EMAIL:
                logger.error("Message type must be EMAIL")
                return False
            
            # Import email libraries
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = message.from_address
            msg["To"] = message.to_address
            if message.subject:
                msg["Subject"] = message.subject
            
            # Add body
            msg.attach(MIMEText(message.body, "plain"))
            
            # Add attachments
            for attachment in message.attachments:
                if "path" in attachment:
                    with open(attachment["path"], "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {attachment.get('filename', 'attachment')}"
                        )
                        msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.smtp_use_tls:
                server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(message.from_address, message.to_address, text)
            server.quit()
            
            message.status = MessageStatus.SENT
            message.sent_at = datetime.now()
            logger.info(f"Email sent successfully to {message.to_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            return False
    
    async def receive_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Receive email messages via IMAP"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            import imaplib
            import email
            from email.header import decode_header
            
            # Connect to IMAP server
            if self.imap_use_ssl:
                mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            else:
                mail = imaplib.IMAP4(self.imap_host, self.imap_port)
            
            mail.login(self.imap_username, self.imap_password)
            mail.select("INBOX")
            
            # Search for messages
            status, messages = mail.search(None, "ALL")
            message_ids = messages[0].split()
            
            # Get recent messages
            recent_ids = message_ids[-(limit + offset):-offset] if offset > 0 else message_ids[-limit:]
            
            messages_list = []
            for msg_id in recent_ids:
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status == "OK":
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Parse email
                    subject = self._decode_header(email_message["Subject"])
                    from_addr = self._decode_header(email_message["From"])
                    to_addr = self._decode_header(email_message["To"])
                    date_str = email_message["Date"]
                    
                    # Get body
                    body = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = email_message.get_payload(decode=True).decode()
                    
                    # Create message object
                    message = Message(
                        id=msg_id.decode(),
                        type=MessageType.EMAIL,
                        from_address=from_addr,
                        to_address=to_addr,
                        subject=subject,
                        body=body,
                        status=MessageStatus.DELIVERED,
                        created_at=datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z") if date_str else datetime.now()
                    )
                    messages_list.append(message)
            
            mail.close()
            mail.logout()
            
            return messages_list
            
        except Exception as e:
            logger.error(f"Error receiving email messages: {e}")
            return []
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode()
            else:
                decoded_string += part
        
        return decoded_string
    
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get email message status (always delivered for received emails)"""
        return MessageStatus.DELIVERED
    
    async def get_contacts(self) -> List[Contact]:
        """Get contacts from email address book (not implemented)"""
        logger.warning("Email contacts not implemented")
        return []


class MessagingServiceManager:
    """Manages multiple messaging services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services: Dict[MessageType, MessagingService] = {}
        self.message_queue: List[Message] = []
        self.message_history: Dict[str, Message] = {}
        
        # Initialize services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize available messaging services"""
        try:
            # Initialize SMS service
            if (self.config.get("twilio_account_sid") and 
                self.config.get("twilio_auth_token") and 
                self.config.get("twilio_from_number")):
                self.services[MessageType.SMS] = SMSService(self.config)
                logger.info("SMS service initialized")
            
            # Initialize Email service
            if (self.config.get("smtp_host") and 
                self.config.get("smtp_username") and 
                self.config.get("smtp_password")):
                self.services[MessageType.EMAIL] = EmailService(self.config)
                logger.info("Email service initialized")
            
            # TODO: Initialize other services (WhatsApp, Telegram, etc.)
            
        except Exception as e:
            logger.error(f"Error initializing messaging services: {e}")
    
    async def authenticate_all(self) -> Dict[MessageType, bool]:
        """Authenticate with all services"""
        results = {}
        for service_type, service in self.services.items():
            try:
                results[service_type] = await service.authenticate()
            except Exception as e:
                logger.error(f"Error authenticating {service_type.value}: {e}")
                results[service_type] = False
        return results
    
    async def send_message(self, message: Message) -> bool:
        """Send message via appropriate service"""
        try:
            if message.type not in self.services:
                logger.error(f"No service available for message type: {message.type.value}")
                return False
            
            service = self.services[message.type]
            if not service.is_authenticated:
                await service.authenticate()
            
            # Add to queue
            self.message_queue.append(message)
            
            # Send message
            success = await service.send_message(message)
            
            # Store in history
            self.message_history[message.id] = message
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def receive_messages(self, message_type: Optional[MessageType] = None, 
                             limit: int = 50) -> List[Message]:
        """Receive messages from services"""
        try:
            all_messages = []
            
            if message_type:
                # Receive from specific service
                if message_type in self.services:
                    service = self.services[message_type]
                    if service.is_authenticated:
                        messages = await service.receive_messages(limit)
                        all_messages.extend(messages)
            else:
                # Receive from all services
                for service_type, service in self.services.items():
                    if service.is_authenticated:
                        try:
                            messages = await service.receive_messages(limit)
                            all_messages.extend(messages)
                        except Exception as e:
                            logger.error(f"Error receiving messages from {service_type.value}: {e}")
            
            # Store in history
            for message in all_messages:
                self.message_history[message.id] = message
            
            return all_messages
            
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            return []
    
    async def get_message_status(self, message_id: str, message_type: MessageType) -> Optional[MessageStatus]:
        """Get message delivery status"""
        try:
            if message_type not in self.services:
                return None
            
            service = self.services[message_type]
            if not service.is_authenticated:
                await service.authenticate()
            
            return await service.get_message_status(message_id)
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return None
    
    async def get_contacts(self, message_type: Optional[MessageType] = None) -> List[Contact]:
        """Get contacts from services"""
        try:
            all_contacts = []
            
            if message_type:
                # Get from specific service
                if message_type in self.services:
                    service = self.services[message_type]
                    if service.is_authenticated:
                        contacts = await service.get_contacts()
                        all_contacts.extend(contacts)
            else:
                # Get from all services
                for service_type, service in self.services.items():
                    if service.is_authenticated:
                        try:
                            contacts = await service.get_contacts()
                            all_contacts.extend(contacts)
                        except Exception as e:
                            logger.error(f"Error getting contacts from {service_type.value}: {e}")
            
            return all_contacts
            
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []
    
    async def close_all(self):
        """Close all services"""
        for service in self.services.values():
            await service.close()
