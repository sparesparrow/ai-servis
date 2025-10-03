"""
Social Media Services Integration
Provides integration with various social media platforms
"""
import asyncio
import logging
import json
import base64
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import aiohttp
import aiofiles

from messaging_service_abstraction import (
    MessagingService, MessageType, Message, MessageStatus, MessagePriority, Contact
)

logger = logging.getLogger(__name__)


class SocialMediaType(Enum):
    """Social media platform types"""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    TWITTER = "twitter"
    SIGNAL = "signal"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"


@dataclass
class SocialMediaPost:
    """Social media post representation"""
    id: str
    platform: SocialMediaType
    content: str
    media_urls: List[str] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    location: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: str = "draft"  # draft, published, scheduled, failed
    engagement: Dict[str, int] = None  # likes, shares, comments, etc.
    created_at: datetime = None
    
    def __post_init__(self):
        if self.media_urls is None:
            self.media_urls = []
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []
        if self.engagement is None:
            self.engagement = {}
        if self.created_at is None:
            self.created_at = datetime.now()


class WhatsAppService(MessagingService):
    """WhatsApp Business API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token = config.get("whatsapp_access_token")
        self.phone_number_id = config.get("whatsapp_phone_number_id")
        self.business_account_id = config.get("whatsapp_business_account_id")
        self.webhook_verify_token = config.get("whatsapp_webhook_verify_token")
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def _get_service_type(self) -> MessageType:
        return MessageType.WHATSAPP
    
    async def authenticate(self) -> bool:
        """Authenticate with WhatsApp Business API"""
        try:
            if not all([self.access_token, self.phone_number_id]):
                logger.error("WhatsApp credentials not configured")
                return False
            
            # Create session with access token
            headers = {"Authorization": f"Bearer {self.access_token}"}
            self.session = aiohttp.ClientSession(headers=headers)
            
            # Test authentication by getting phone number info
            url = f"{self.base_url}/{self.phone_number_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    self.is_authenticated = True
                    logger.info("WhatsApp Business API authentication successful")
                    return True
                else:
                    logger.error(f"WhatsApp authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with WhatsApp: {e}")
            return False
    
    async def send_message(self, message: Message) -> bool:
        """Send WhatsApp message"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            if message.type != MessageType.WHATSAPP:
                logger.error("Message type must be WHATSAPP")
                return False
            
            # Prepare WhatsApp API request
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            # Create message payload
            payload = {
                "messaging_product": "whatsapp",
                "to": message.to_address,
                "type": "text",
                "text": {"body": message.body}
            }
            
            # Add media if attachments exist
            if message.attachments:
                # For now, handle first attachment as image
                attachment = message.attachments[0]
                if "url" in attachment:
                    payload["type"] = "image"
                    payload["image"] = {
                        "link": attachment["url"],
                        "caption": message.body
                    }
                elif "path" in attachment:
                    # Upload media first
                    media_id = await self._upload_media(attachment["path"])
                    if media_id:
                        payload["type"] = "image"
                        payload["image"] = {
                            "id": media_id,
                            "caption": message.body
                        }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    message.id = result["messages"][0]["id"]
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.now()
                    logger.info(f"WhatsApp message sent successfully: {message.id}")
                    return True
                else:
                    error_data = await response.json()
                    message.status = MessageStatus.FAILED
                    message.error_message = f"WhatsApp error: {error_data}"
                    logger.error(f"Failed to send WhatsApp message: {response.status} - {error_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            return False
    
    async def _upload_media(self, file_path: str) -> Optional[str]:
        """Upload media file to WhatsApp"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/media"
            
            # Read file
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('messaging_product', 'whatsapp')
            data.add_field('file', file_data, filename=file_path.split('/')[-1])
            
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["id"]
                else:
                    logger.error(f"Failed to upload media: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            return None
    
    async def receive_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Receive WhatsApp messages (requires webhook setup)"""
        # WhatsApp uses webhooks for receiving messages
        # This would need to be implemented with a webhook endpoint
        logger.warning("WhatsApp message receiving requires webhook setup")
        return []
    
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get WhatsApp message status"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            url = f"{self.base_url}/{self.phone_number_id}/messages/{message_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get("status", "unknown")
                    
                    status_map = {
                        "sent": MessageStatus.SENT,
                        "delivered": MessageStatus.DELIVERED,
                        "read": MessageStatus.READ,
                        "failed": MessageStatus.FAILED
                    }
                    
                    return status_map.get(status, MessageStatus.PENDING)
                else:
                    logger.error(f"Failed to get WhatsApp message status: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting WhatsApp message status: {e}")
            return None
    
    async def get_contacts(self) -> List[Contact]:
        """Get WhatsApp contacts (not directly supported by API)"""
        logger.warning("WhatsApp contacts not directly supported by Business API")
        return []


class TelegramService(MessagingService):
    """Telegram Bot API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get("telegram_bot_token")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def _get_service_type(self) -> MessageType:
        return MessageType.TELEGRAM
    
    async def authenticate(self) -> bool:
        """Authenticate with Telegram Bot API"""
        try:
            if not self.bot_token:
                logger.error("Telegram bot token not configured")
                return False
            
            # Create session
            self.session = aiohttp.ClientSession()
            
            # Test authentication by getting bot info
            url = f"{self.base_url}/getMe"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        self.is_authenticated = True
                        logger.info(f"Telegram bot authentication successful: {data['result']['username']}")
                        return True
                    else:
                        logger.error(f"Telegram authentication failed: {data}")
                        return False
                else:
                    logger.error(f"Telegram authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with Telegram: {e}")
            return False
    
    async def send_message(self, message: Message) -> bool:
        """Send Telegram message"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            if message.type != MessageType.TELEGRAM:
                logger.error("Message type must be TELEGRAM")
                return False
            
            # Prepare Telegram API request
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": message.to_address,
                "text": message.body,
                "parse_mode": "HTML"  # Support HTML formatting
            }
            
            # Add reply markup if needed
            if message.metadata and "reply_markup" in message.metadata:
                payload["reply_markup"] = message.metadata["reply_markup"]
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        result = data["result"]
                        message.id = str(result["message_id"])
                        message.status = MessageStatus.SENT
                        message.sent_at = datetime.now()
                        logger.info(f"Telegram message sent successfully: {message.id}")
                        return True
                    else:
                        message.status = MessageStatus.FAILED
                        message.error_message = f"Telegram error: {data}"
                        logger.error(f"Failed to send Telegram message: {data}")
                        return False
                else:
                    message.status = MessageStatus.FAILED
                    message.error_message = f"HTTP error: {response.status}"
                    logger.error(f"Failed to send Telegram message: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            return False
    
    async def receive_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Receive Telegram messages via getUpdates"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            url = f"{self.base_url}/getUpdates"
            params = {
                "limit": min(limit, 100),  # Telegram max
                "offset": offset
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        messages = []
                        for update in data.get("result", []):
                            if "message" in update:
                                msg_data = update["message"]
                                
                                # Extract message content
                                text = ""
                                if "text" in msg_data:
                                    text = msg_data["text"]
                                elif "caption" in msg_data:
                                    text = msg_data["caption"]
                                
                                message = Message(
                                    id=str(msg_data["message_id"]),
                                    type=MessageType.TELEGRAM,
                                    from_address=str(msg_data["from"]["id"]),
                                    to_address=str(msg_data["chat"]["id"]),
                                    body=text,
                                    status=MessageStatus.DELIVERED,
                                    created_at=datetime.fromtimestamp(msg_data["date"]),
                                    metadata={
                                        "chat_type": msg_data["chat"]["type"],
                                        "from_username": msg_data["from"].get("username"),
                                        "from_first_name": msg_data["from"].get("first_name")
                                    }
                                )
                                messages.append(message)
                        
                        return messages
                    else:
                        logger.error(f"Telegram getUpdates failed: {data}")
                        return []
                else:
                    logger.error(f"Failed to get Telegram updates: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error receiving Telegram messages: {e}")
            return []
    
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get Telegram message status (always delivered for sent messages)"""
        return MessageStatus.DELIVERED
    
    async def get_contacts(self) -> List[Contact]:
        """Get Telegram contacts (not directly supported by Bot API)"""
        logger.warning("Telegram contacts not directly supported by Bot API")
        return []


class TwitterService(MessagingService):
    """Twitter/X API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bearer_token = config.get("twitter_bearer_token")
        self.api_key = config.get("twitter_api_key")
        self.api_secret = config.get("twitter_api_secret")
        self.access_token = config.get("twitter_access_token")
        self.access_token_secret = config.get("twitter_access_token_secret")
        self.base_url = "https://api.twitter.com/2"
    
    def _get_service_type(self) -> MessageType:
        return MessageType.TWITTER
    
    async def authenticate(self) -> bool:
        """Authenticate with Twitter API"""
        try:
            if not self.bearer_token:
                logger.error("Twitter bearer token not configured")
                return False
            
            # Create session with bearer token
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            self.session = aiohttp.ClientSession(headers=headers)
            
            # Test authentication by getting user info
            url = f"{self.base_url}/users/me"
            async with self.session.get(url) as response:
                if response.status == 200:
                    self.is_authenticated = True
                    logger.info("Twitter API authentication successful")
                    return True
                else:
                    logger.error(f"Twitter authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with Twitter: {e}")
            return False
    
    async def send_message(self, message: Message) -> bool:
        """Send Twitter post/tweet"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            if message.type != MessageType.TWITTER:
                logger.error("Message type must be TWITTER")
                return False
            
            # Prepare Twitter API request
            url = f"{self.base_url}/tweets"
            
            payload = {
                "text": message.body[:280]  # Twitter character limit
            }
            
            # Add reply context if replying to a tweet
            if message.metadata and "reply_to_tweet_id" in message.metadata:
                payload["reply"] = {
                    "in_reply_to_tweet_id": message.metadata["reply_to_tweet_id"]
                }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    message.id = data["data"]["id"]
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.now()
                    logger.info(f"Twitter post sent successfully: {message.id}")
                    return True
                else:
                    error_data = await response.json()
                    message.status = MessageStatus.FAILED
                    message.error_message = f"Twitter error: {error_data}"
                    logger.error(f"Failed to send Twitter post: {response.status} - {error_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Twitter post: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            return False
    
    async def receive_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Receive Twitter mentions/DMs"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            # Get mentions
            url = f"{self.base_url}/users/me/mentions"
            params = {
                "max_results": min(limit, 100),
                "tweet.fields": "created_at,author_id"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    messages = []
                    
                    for tweet in data.get("data", []):
                        message = Message(
                            id=tweet["id"],
                            type=MessageType.TWITTER,
                            from_address=tweet["author_id"],
                            to_address="me",  # Mentions are directed to the bot
                            body=tweet["text"],
                            status=MessageStatus.DELIVERED,
                            created_at=datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
                        )
                        messages.append(message)
                    
                    return messages
                else:
                    logger.error(f"Failed to get Twitter mentions: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error receiving Twitter messages: {e}")
            return []
    
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get Twitter post status"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            url = f"{self.base_url}/tweets/{message_id}"
            params = {"tweet.fields": "public_metrics"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data:
                        # Tweet exists, consider it delivered
                        return MessageStatus.DELIVERED
                    else:
                        return MessageStatus.FAILED
                else:
                    logger.error(f"Failed to get Twitter post status: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Twitter post status: {e}")
            return None
    
    async def get_contacts(self) -> List[Contact]:
        """Get Twitter followers"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            # Get followers
            url = f"{self.base_url}/users/me/followers"
            params = {"max_results": 100}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    contacts = []
                    
                    for user in data.get("data", []):
                        contact = Contact(
                            id=user["id"],
                            name=user.get("name", ""),
                            metadata={
                                "username": user.get("username"),
                                "followers_count": user.get("public_metrics", {}).get("followers_count", 0)
                            }
                        )
                        contacts.append(contact)
                    
                    return contacts
                else:
                    logger.error(f"Failed to get Twitter followers: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting Twitter contacts: {e}")
            return []


class SignalService(MessagingService):
    """Signal API integration (using Signal REST API)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.signal_server_url = config.get("signal_server_url", "http://localhost:8080")
        self.phone_number = config.get("signal_phone_number")
        self.password = config.get("signal_password")
    
    def _get_service_type(self) -> MessageType:
        return MessageType.SIGNAL
    
    async def authenticate(self) -> bool:
        """Authenticate with Signal server"""
        try:
            if not all([self.phone_number, self.password]):
                logger.error("Signal credentials not configured")
                return False
            
            # Create session
            self.session = aiohttp.ClientSession()
            
            # Register device (if not already registered)
            url = f"{self.signal_server_url}/v1/register/{self.phone_number}"
            data = {"password": self.password}
            
            async with self.session.post(url, json=data) as response:
                if response.status in [200, 400]:  # 400 if already registered
                    self.is_authenticated = True
                    logger.info("Signal authentication successful")
                    return True
                else:
                    logger.error(f"Signal authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with Signal: {e}")
            return False
    
    async def send_message(self, message: Message) -> bool:
        """Send Signal message"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            if message.type != MessageType.SIGNAL:
                logger.error("Message type must be SIGNAL")
                return False
            
            # Prepare Signal API request
            url = f"{self.signal_server_url}/v1/send"
            
            payload = {
                "username": self.phone_number,
                "password": self.password,
                "recipients": [message.to_address],
                "message": message.body
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    message.id = str(data.get("timestamp", datetime.now().timestamp()))
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.now()
                    logger.info(f"Signal message sent successfully: {message.id}")
                    return True
                else:
                    error_data = await response.text()
                    message.status = MessageStatus.FAILED
                    message.error_message = f"Signal error: {error_data}"
                    logger.error(f"Failed to send Signal message: {response.status} - {error_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Signal message: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            return False
    
    async def receive_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Receive Signal messages (requires webhook setup)"""
        # Signal uses webhooks for receiving messages
        logger.warning("Signal message receiving requires webhook setup")
        return []
    
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get Signal message status (always delivered for sent messages)"""
        return MessageStatus.DELIVERED
    
    async def get_contacts(self) -> List[Contact]:
        """Get Signal contacts (not directly supported by API)"""
        logger.warning("Signal contacts not directly supported by API")
        return []


class FacebookMessengerService(MessagingService):
    """Facebook Messenger API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.page_access_token = config.get("facebook_page_access_token")
        self.app_secret = config.get("facebook_app_secret")
        self.verify_token = config.get("facebook_verify_token")
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def _get_service_type(self) -> MessageType:
        return MessageType.FACEBOOK
    
    async def authenticate(self) -> bool:
        """Authenticate with Facebook Messenger API"""
        try:
            if not self.page_access_token:
                logger.error("Facebook page access token not configured")
                return False
            
            # Create session with access token
            headers = {"Authorization": f"Bearer {self.page_access_token}"}
            self.session = aiohttp.ClientSession(headers=headers)
            
            # Test authentication by getting page info
            url = f"{self.base_url}/me"
            async with self.session.get(url) as response:
                if response.status == 200:
                    self.is_authenticated = True
                    logger.info("Facebook Messenger API authentication successful")
                    return True
                else:
                    logger.error(f"Facebook authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with Facebook: {e}")
            return False
    
    async def send_message(self, message: Message) -> bool:
        """Send Facebook Messenger message"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            if message.type != MessageType.FACEBOOK:
                logger.error("Message type must be FACEBOOK")
                return False
            
            # Prepare Facebook API request
            url = f"{self.base_url}/me/messages"
            
            payload = {
                "recipient": {"id": message.to_address},
                "message": {"text": message.body}
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    message.id = data["message_id"]
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.now()
                    logger.info(f"Facebook message sent successfully: {message.id}")
                    return True
                else:
                    error_data = await response.json()
                    message.status = MessageStatus.FAILED
                    message.error_message = f"Facebook error: {error_data}"
                    logger.error(f"Failed to send Facebook message: {response.status} - {error_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Facebook message: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            return False
    
    async def receive_messages(self, limit: int = 50, offset: int = 0) -> List[Message]:
        """Receive Facebook Messenger messages (requires webhook setup)"""
        # Facebook uses webhooks for receiving messages
        logger.warning("Facebook message receiving requires webhook setup")
        return []
    
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get Facebook message status (always delivered for sent messages)"""
        return MessageStatus.DELIVERED
    
    async def get_contacts(self) -> List[Contact]:
        """Get Facebook page followers"""
        try:
            if not self.is_authenticated:
                await self.authenticate()
            
            # Get page followers
            url = f"{self.base_url}/me/subscribers"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    contacts = []
                    
                    for user in data.get("data", []):
                        contact = Contact(
                            id=user["id"],
                            name=user.get("name", ""),
                            metadata={
                                "first_name": user.get("first_name"),
                                "last_name": user.get("last_name")
                            }
                        )
                        contacts.append(contact)
                    
                    return contacts
                else:
                    logger.error(f"Failed to get Facebook followers: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting Facebook contacts: {e}")
            return []


class SocialMediaServiceManager:
    """Manages social media services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services: Dict[MessageType, MessagingService] = {}
        
        # Initialize services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize available social media services"""
        try:
            # Initialize WhatsApp
            if (self.config.get("whatsapp_access_token") and 
                self.config.get("whatsapp_phone_number_id")):
                self.services[MessageType.WHATSAPP] = WhatsAppService(self.config)
                logger.info("WhatsApp service initialized")
            
            # Initialize Telegram
            if self.config.get("telegram_bot_token"):
                self.services[MessageType.TELEGRAM] = TelegramService(self.config)
                logger.info("Telegram service initialized")
            
            # Initialize Twitter
            if self.config.get("twitter_bearer_token"):
                self.services[MessageType.TWITTER] = TwitterService(self.config)
                logger.info("Twitter service initialized")
            
            # Initialize Signal
            if (self.config.get("signal_phone_number") and 
                self.config.get("signal_password")):
                self.services[MessageType.SIGNAL] = SignalService(self.config)
                logger.info("Signal service initialized")
            
            # Initialize Facebook Messenger
            if self.config.get("facebook_page_access_token"):
                self.services[MessageType.FACEBOOK] = FacebookMessengerService(self.config)
                logger.info("Facebook Messenger service initialized")
            
        except Exception as e:
            logger.error(f"Error initializing social media services: {e}")
    
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
            
            return await service.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending social media message: {e}")
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
            
            return all_messages
            
        except Exception as e:
            logger.error(f"Error receiving social media messages: {e}")
            return []
    
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
            logger.error(f"Error getting social media contacts: {e}")
            return []
    
    async def close_all(self):
        """Close all services"""
        for service in self.services.values():
            await service.close()
