"""
Response Formatter for Command Processing
Formats responses for different interface types
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from command_models import CommandResult, Command, IntentType

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formats responses for different interface types"""
    
    def __init__(self):
        self.interface_templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize response templates for different interfaces"""
        return {
            "voice": {
                "success": {
                    "template": "{response}",
                    "max_length": 100,
                    "include_suggestions": True,
                    "suggestion_prefix": "You can also say: "
                },
                "error": {
                    "template": "Sorry, {error_message}",
                    "max_length": 80,
                    "include_suggestions": False
                },
                "status": {
                    "template": "{status}",
                    "max_length": 60,
                    "include_suggestions": False
                }
            },
            "text": {
                "success": {
                    "template": "✅ {response}",
                    "max_length": 500,
                    "include_suggestions": True,
                    "suggestion_prefix": "Suggestions: "
                },
                "error": {
                    "template": "❌ Error: {error_message}",
                    "max_length": 300,
                    "include_suggestions": False
                },
                "status": {
                    "template": "ℹ️ {status}",
                    "max_length": 200,
                    "include_suggestions": False
                }
            },
            "web": {
                "success": {
                    "template": "{response}",
                    "max_length": 1000,
                    "include_suggestions": True,
                    "suggestion_prefix": "Try these commands: ",
                    "include_metadata": True
                },
                "error": {
                    "template": "Error: {error_message}",
                    "max_length": 500,
                    "include_suggestions": False,
                    "include_metadata": True
                },
                "status": {
                    "template": "{status}",
                    "max_length": 300,
                    "include_suggestions": False,
                    "include_metadata": True
                }
            },
            "mobile": {
                "success": {
                    "template": "{response}",
                    "max_length": 200,
                    "include_suggestions": True,
                    "suggestion_prefix": "Quick actions: ",
                    "include_metadata": True
                },
                "error": {
                    "template": "Error: {error_message}",
                    "max_length": 150,
                    "include_suggestions": False,
                    "include_metadata": True
                },
                "status": {
                    "template": "{status}",
                    "max_length": 100,
                    "include_suggestions": False,
                    "include_metadata": True
                }
            }
        }
    
    async def format_response(self, result: CommandResult, interface_type: str) -> Dict[str, Any]:
        """Format response for specific interface"""
        try:
            template_config = self.interface_templates.get(interface_type, self.interface_templates["text"])
            
            if result.success:
                return await self._format_success_response(result, template_config, interface_type)
            else:
                return await self._format_error_response(result, template_config, interface_type)
                
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return {
                "success": False,
                "response": "Error formatting response",
                "interface_type": interface_type,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _format_success_response(self, result: CommandResult, template_config: Dict[str, Any], interface_type: str) -> Dict[str, Any]:
        """Format successful response"""
        response_data = {
            "success": True,
            "response": result.response,
            "interface_type": interface_type,
            "timestamp": result.timestamp.isoformat(),
            "execution_time": result.execution_time
        }
        
        # Apply template
        template = template_config["success"]["template"]
        formatted_response = template.format(
            response=result.response,
            execution_time=result.execution_time,
            service=result.service_used or "unknown"
        )
        
        # Truncate if necessary
        max_length = template_config["success"]["max_length"]
        if len(formatted_response) > max_length:
            formatted_response = formatted_response[:max_length-3] + "..."
        
        response_data["formatted_response"] = formatted_response
        
        # Add suggestions if configured
        if template_config["success"]["include_suggestions"] and result.suggestions:
            suggestions = self._format_suggestions(result.suggestions, template_config["success"]["suggestion_prefix"])
            response_data["suggestions"] = suggestions
        
        # Add metadata if configured
        if template_config["success"].get("include_metadata", False):
            response_data["metadata"] = {
                "service_used": result.service_used,
                "execution_time": result.execution_time,
                "data": result.data
            }
        
        # Add interface-specific formatting
        if interface_type == "voice":
            response_data = self._format_voice_response(response_data, result)
        elif interface_type == "web":
            response_data = self._format_web_response(response_data, result)
        elif interface_type == "mobile":
            response_data = self._format_mobile_response(response_data, result)
        
        return response_data
    
    async def _format_error_response(self, result: CommandResult, template_config: Dict[str, Any], interface_type: str) -> Dict[str, Any]:
        """Format error response"""
        error_message = result.response
        if result.error_details:
            error_type = result.error_details.get("type", "unknown")
            error_message = f"{error_type}: {error_message}"
        
        response_data = {
            "success": False,
            "response": error_message,
            "interface_type": interface_type,
            "timestamp": result.timestamp.isoformat(),
            "execution_time": result.execution_time
        }
        
        # Apply template
        template = template_config["error"]["template"]
        formatted_response = template.format(
            error_message=error_message,
            execution_time=result.execution_time
        )
        
        # Truncate if necessary
        max_length = template_config["error"]["max_length"]
        if len(formatted_response) > max_length:
            formatted_response = formatted_response[:max_length-3] + "..."
        
        response_data["formatted_response"] = formatted_response
        
        # Add metadata if configured
        if template_config["error"].get("include_metadata", False):
            response_data["metadata"] = {
                "error_details": result.error_details,
                "execution_time": result.execution_time
            }
        
        return response_data
    
    def _format_suggestions(self, suggestions: List[str], prefix: str) -> List[str]:
        """Format suggestions for display"""
        if not suggestions:
            return []
        
        # Limit number of suggestions
        max_suggestions = 5
        limited_suggestions = suggestions[:max_suggestions]
        
        # Format suggestions
        formatted_suggestions = []
        for suggestion in limited_suggestions:
            formatted_suggestions.append(f"{prefix}{suggestion}")
        
        return formatted_suggestions
    
    def _format_voice_response(self, response_data: Dict[str, Any], result: CommandResult) -> Dict[str, Any]:
        """Format response specifically for voice interface"""
        # Add voice-specific metadata
        response_data["voice_metadata"] = {
            "speech_rate": "normal",
            "volume": "normal",
            "pause_before_suggestions": True,
            "confirmation_required": False
        }
        
        # Add audio cues for different types of responses
        if result.data.get("action") == "play":
            response_data["voice_metadata"]["audio_cue"] = "music_start"
        elif result.data.get("action") == "stop":
            response_data["voice_metadata"]["audio_cue"] = "music_stop"
        elif "error" in response_data["response"].lower():
            response_data["voice_metadata"]["audio_cue"] = "error"
        
        return response_data
    
    def _format_web_response(self, response_data: Dict[str, Any], result: CommandResult) -> Dict[str, Any]:
        """Format response specifically for web interface"""
        # Add web-specific metadata
        response_data["web_metadata"] = {
            "show_timestamp": True,
            "show_execution_time": True,
            "show_service_info": True,
            "auto_refresh": False,
            "notification_type": "success" if result.success else "error"
        }
        
        # Add rich formatting for web
        if result.data:
            response_data["rich_data"] = self._format_rich_data(result.data)
        
        # Add action buttons for web interface
        if result.suggestions:
            response_data["action_buttons"] = [
                {"text": suggestion, "action": "quick_command", "command": suggestion}
                for suggestion in result.suggestions[:3]
            ]
        
        return response_data
    
    def _format_mobile_response(self, response_data: Dict[str, Any], result: CommandResult) -> Dict[str, Any]:
        """Format response specifically for mobile interface"""
        # Add mobile-specific metadata
        response_data["mobile_metadata"] = {
            "notification": True,
            "vibration": False,
            "sound": "default",
            "priority": "normal"
        }
        
        # Add quick actions for mobile
        if result.suggestions:
            response_data["quick_actions"] = [
                {"title": suggestion, "action": "command", "value": suggestion}
                for suggestion in result.suggestions[:3]
            ]
        
        # Add push notification data
        response_data["push_notification"] = {
            "title": "AI-SERVIS",
            "body": response_data["formatted_response"],
            "data": {
                "command_id": result.command_id,
                "success": result.success
            }
        }
        
        return response_data
    
    def _format_rich_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format rich data for web interface"""
        rich_data = {}
        
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                rich_data[key] = {
                    "type": "text",
                    "value": str(value),
                    "display": key.replace("_", " ").title()
                }
            elif isinstance(value, list):
                rich_data[key] = {
                    "type": "list",
                    "value": value,
                    "display": key.replace("_", " ").title()
                }
            elif isinstance(value, dict):
                rich_data[key] = {
                    "type": "object",
                    "value": value,
                    "display": key.replace("_", " ").title()
                }
            else:
                rich_data[key] = {
                    "type": "unknown",
                    "value": str(value),
                    "display": key.replace("_", " ").title()
                }
        
        return rich_data
    
    async def format_status_response(self, status: str, interface_type: str, **kwargs) -> Dict[str, Any]:
        """Format status response"""
        template_config = self.interface_templates.get(interface_type, self.interface_templates["text"])
        
        response_data = {
            "success": True,
            "response": status,
            "interface_type": interface_type,
            "timestamp": datetime.now().isoformat(),
            "type": "status"
        }
        
        # Apply template
        template = template_config["status"]["template"]
        formatted_response = template.format(
            status=status,
            **kwargs
        )
        
        # Truncate if necessary
        max_length = template_config["status"]["max_length"]
        if len(formatted_response) > max_length:
            formatted_response = formatted_response[:max_length-3] + "..."
        
        response_data["formatted_response"] = formatted_response
        
        return response_data
    
    async def format_notification_response(self, title: str, message: str, interface_type: str, level: str = "info") -> Dict[str, Any]:
        """Format notification response"""
        response_data = {
            "success": True,
            "response": f"{title}: {message}",
            "interface_type": interface_type,
            "timestamp": datetime.now().isoformat(),
            "type": "notification",
            "notification": {
                "title": title,
                "message": message,
                "level": level
            }
        }
        
        # Interface-specific formatting
        if interface_type == "voice":
            response_data["formatted_response"] = f"{title}. {message}"
        elif interface_type == "text":
            response_data["formatted_response"] = f"📢 {title}: {message}"
        elif interface_type == "web":
            response_data["formatted_response"] = f"{title}: {message}"
            response_data["web_metadata"] = {
                "notification_type": level,
                "show_timestamp": True,
                "auto_dismiss": True
            }
        elif interface_type == "mobile":
            response_data["formatted_response"] = f"{title}: {message}"
            response_data["push_notification"] = {
                "title": title,
                "body": message,
                "priority": "high" if level == "error" else "normal"
            }
        
        return response_data
    
    def get_interface_capabilities(self, interface_type: str) -> Dict[str, Any]:
        """Get capabilities for specific interface"""
        capabilities = {
            "voice": {
                "max_response_length": 100,
                "supports_suggestions": True,
                "supports_rich_data": False,
                "supports_notifications": True,
                "supports_audio_cues": True
            },
            "text": {
                "max_response_length": 500,
                "supports_suggestions": True,
                "supports_rich_data": False,
                "supports_notifications": True,
                "supports_audio_cues": False
            },
            "web": {
                "max_response_length": 1000,
                "supports_suggestions": True,
                "supports_rich_data": True,
                "supports_notifications": True,
                "supports_audio_cues": False
            },
            "mobile": {
                "max_response_length": 200,
                "supports_suggestions": True,
                "supports_rich_data": True,
                "supports_notifications": True,
                "supports_audio_cues": False
            }
        }
        
        return capabilities.get(interface_type, capabilities["text"])
