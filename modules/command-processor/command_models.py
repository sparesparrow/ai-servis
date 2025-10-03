"""
Command Processing Models and Interfaces
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from pydantic import BaseModel, Field, validator
import asyncio
import uuid
import json


class CommandStatus(str, Enum):
    """Command processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class CommandPriority(int, Enum):
    """Command priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class IntentType(str, Enum):
    """Intent classification types"""
    AUDIO_CONTROL = "audio_control"
    SYSTEM_CONTROL = "system_control"
    SMART_HOME = "smart_home"
    COMMUNICATION = "communication"
    NAVIGATION = "navigation"
    INFORMATION = "information"
    FILE_OPERATION = "file_operation"
    HARDWARE_CONTROL = "hardware_control"
    UNKNOWN = "unknown"


class ParameterType(str, Enum):
    """Parameter types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    TIME = "time"
    FILE_PATH = "file_path"


class Command(BaseModel):
    """Base command model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique command ID")
    text: str = Field(..., description="Original command text")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    interface_type: str = Field(..., description="Interface type (voice, text, web, mobile)")
    priority: CommandPriority = Field(default=CommandPriority.NORMAL, description="Command priority")
    status: CommandStatus = Field(default=CommandStatus.PENDING, description="Command status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    timeout: int = Field(default=30, description="Command timeout in seconds")
    context: Dict[str, Any] = Field(default_factory=dict, description="Command context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True


class ParsedCommand(Command):
    """Command after parsing and validation"""
    intent: IntentType = Field(..., description="Classified intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Intent confidence score")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters")
    validated_parameters: Dict[str, Any] = Field(default_factory=dict, description="Validated parameters")
    alternatives: List[Tuple[str, float]] = Field(default_factory=list, description="Alternative intents")
    processing_time: float = Field(default=0.0, description="Processing time in seconds")
    errors: List[str] = Field(default_factory=list, description="Processing errors")


class CommandResult(BaseModel):
    """Command execution result"""
    command_id: str = Field(..., description="Command ID")
    success: bool = Field(..., description="Whether command was successful")
    response: str = Field(..., description="Response text")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up commands")
    execution_time: float = Field(..., description="Execution time in seconds")
    service_used: Optional[str] = Field(None, description="Service that handled the command")
    timestamp: datetime = Field(default_factory=datetime.now, description="Result timestamp")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")


class ParameterSchema(BaseModel):
    """Parameter validation schema"""
    name: str = Field(..., description="Parameter name")
    type: ParameterType = Field(..., description="Parameter type")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Any = Field(None, description="Default value")
    min_value: Optional[Union[int, float]] = Field(None, description="Minimum value")
    max_value: Optional[Union[int, float]] = Field(None, description="Maximum value")
    pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    choices: Optional[List[Any]] = Field(None, description="Valid choices")
    description: str = Field("", description="Parameter description")


class IntentSchema(BaseModel):
    """Intent classification schema"""
    intent: IntentType = Field(..., description="Intent type")
    keywords: List[str] = Field(..., description="Keywords for intent detection")
    parameters: List[ParameterSchema] = Field(default_factory=list, description="Expected parameters")
    service: str = Field(..., description="Service that handles this intent")
    tool: str = Field(..., description="Tool/function to call")
    description: str = Field("", description="Intent description")
    examples: List[str] = Field(default_factory=list, description="Example commands")


class CommandQueue(BaseModel):
    """Command queue for prioritization"""
    commands: List[Command] = Field(default_factory=list, description="Queued commands")
    max_size: int = Field(default=1000, description="Maximum queue size")
    processing_limit: int = Field(default=10, description="Maximum concurrent processing")
    
    def add_command(self, command: Command) -> bool:
        """Add command to queue"""
        if len(self.commands) >= self.max_size:
            return False
        
        # Insert command based on priority
        inserted = False
        for i, existing_command in enumerate(self.commands):
            if command.priority > existing_command.priority:
                self.commands.insert(i, command)
                inserted = True
                break
        
        if not inserted:
            self.commands.append(command)
        
        return True
    
    def get_next_command(self) -> Optional[Command]:
        """Get next command from queue"""
        if self.commands:
            return self.commands.pop(0)
        return None
    
    def remove_command(self, command_id: str) -> bool:
        """Remove command from queue"""
        for i, command in enumerate(self.commands):
            if command.id == command_id:
                del self.commands[i]
                return True
        return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            "total_commands": len(self.commands),
            "max_size": self.max_size,
            "processing_limit": self.processing_limit,
            "priority_distribution": {
                priority.name: sum(1 for cmd in self.commands if cmd.priority == priority)
                for priority in CommandPriority
            }
        }


class CommandProcessor(ABC):
    """Abstract command processor"""
    
    @abstractmethod
    async def parse_command(self, command: Command) -> ParsedCommand:
        """Parse and validate command"""
        pass
    
    @abstractmethod
    async def execute_command(self, parsed_command: ParsedCommand) -> CommandResult:
        """Execute parsed command"""
        pass
    
    @abstractmethod
    async def validate_parameters(self, parameters: Dict[str, Any], schema: List[ParameterSchema]) -> Dict[str, Any]:
        """Validate command parameters"""
        pass


class IntentClassifier(ABC):
    """Abstract intent classifier"""
    
    @abstractmethod
    async def classify_intent(self, text: str, context: Dict[str, Any]) -> Tuple[IntentType, float, List[Tuple[str, float]]]:
        """Classify command intent"""
        pass
    
    @abstractmethod
    async def extract_parameters(self, text: str, intent: IntentType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from command text"""
        pass


class ParameterExtractor(ABC):
    """Abstract parameter extractor"""
    
    @abstractmethod
    async def extract_parameters(self, text: str, intent: IntentType, schema: List[ParameterSchema]) -> Dict[str, Any]:
        """Extract parameters from text"""
        pass
    
    @abstractmethod
    async def validate_parameter(self, value: Any, schema: ParameterSchema) -> Tuple[bool, Any, str]:
        """Validate single parameter"""
        pass


class ResponseFormatter(ABC):
    """Abstract response formatter"""
    
    @abstractmethod
    async def format_response(self, result: CommandResult, interface_type: str) -> Dict[str, Any]:
        """Format response for specific interface"""
        pass
    
    @abstractmethod
    async def format_error(self, error: Exception, command: Command) -> Dict[str, Any]:
        """Format error response"""
        pass


class CommandValidator:
    """Command validation utilities"""
    
    @staticmethod
    def validate_command_text(text: str) -> Tuple[bool, List[str]]:
        """Validate command text"""
        errors = []
        
        if not text or not text.strip():
            errors.append("Command text cannot be empty")
        
        if len(text) > 1000:
            errors.append("Command text too long (max 1000 characters)")
        
        # Check for potentially harmful content
        dangerous_patterns = [
            r'rm\s+-rf',
            r'del\s+/s',
            r'format\s+',
            r'shutdown\s+',
            r'reboot\s+'
        ]
        
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(f"Potentially dangerous command detected: {pattern}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_parameters(parameters: Dict[str, Any], schema: List[ParameterSchema]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Validate parameters against schema"""
        errors = []
        validated_params = {}
        
        for param_schema in schema:
            param_name = param_schema.name
            param_value = parameters.get(param_name, param_schema.default)
            
            if param_schema.required and param_value is None:
                errors.append(f"Required parameter '{param_name}' is missing")
                continue
            
            if param_value is not None:
                # Type validation
                if param_schema.type == ParameterType.INTEGER:
                    try:
                        param_value = int(param_value)
                    except (ValueError, TypeError):
                        errors.append(f"Parameter '{param_name}' must be an integer")
                        continue
                
                elif param_schema.type == ParameterType.FLOAT:
                    try:
                        param_value = float(param_value)
                    except (ValueError, TypeError):
                        errors.append(f"Parameter '{param_name}' must be a float")
                        continue
                
                elif param_schema.type == ParameterType.BOOLEAN:
                    if isinstance(param_value, str):
                        param_value = param_value.lower() in ['true', '1', 'yes', 'on']
                    elif not isinstance(param_value, bool):
                        errors.append(f"Parameter '{param_name}' must be a boolean")
                        continue
                
                # Range validation
                if param_schema.min_value is not None and param_value < param_schema.min_value:
                    errors.append(f"Parameter '{param_name}' must be >= {param_schema.min_value}")
                
                if param_schema.max_value is not None and param_value > param_schema.max_value:
                    errors.append(f"Parameter '{param_name}' must be <= {param_schema.max_value}")
                
                # Pattern validation
                if param_schema.pattern:
                    import re
                    if not re.match(param_schema.pattern, str(param_value)):
                        errors.append(f"Parameter '{param_name}' does not match required pattern")
                
                # Choices validation
                if param_schema.choices and param_value not in param_schema.choices:
                    errors.append(f"Parameter '{param_name}' must be one of: {param_schema.choices}")
            
            validated_params[param_name] = param_value
        
        return len(errors) == 0, validated_params, errors


class CommandMetrics:
    """Command processing metrics"""
    
    def __init__(self):
        self.total_commands = 0
        self.successful_commands = 0
        self.failed_commands = 0
        self.total_processing_time = 0.0
        self.intent_classification_time = 0.0
        self.parameter_extraction_time = 0.0
        self.execution_time = 0.0
        self.intent_distribution = {}
        self.interface_distribution = {}
        self.error_distribution = {}
        self.average_response_time = 0.0
    
    def record_command(self, command: Command, result: CommandResult):
        """Record command processing metrics"""
        self.total_commands += 1
        
        if result.success:
            self.successful_commands += 1
        else:
            self.failed_commands += 1
        
        self.total_processing_time += result.execution_time
        
        # Update distributions
        if hasattr(command, 'intent'):
            intent = command.intent
            self.intent_distribution[intent] = self.intent_distribution.get(intent, 0) + 1
        
        interface = command.interface_type
        self.interface_distribution[interface] = self.interface_distribution.get(interface, 0) + 1
        
        if not result.success and result.error_details:
            error_type = result.error_details.get('type', 'unknown')
            self.error_distribution[error_type] = self.error_distribution.get(error_type, 0) + 1
        
        # Update average response time
        self.average_response_time = self.total_processing_time / self.total_commands
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            "total_commands": self.total_commands,
            "successful_commands": self.successful_commands,
            "failed_commands": self.failed_commands,
            "success_rate": self.successful_commands / max(self.total_commands, 1),
            "average_response_time": self.average_response_time,
            "total_processing_time": self.total_processing_time,
            "intent_distribution": self.intent_distribution,
            "interface_distribution": self.interface_distribution,
            "error_distribution": self.error_distribution
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.__init__()


class CommandCache:
    """Command result caching"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, Tuple[CommandResult, datetime]] = {}
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
    
    def get(self, command_id: str) -> Optional[CommandResult]:
        """Get cached command result"""
        if command_id in self.cache:
            result, timestamp = self.cache[command_id]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return result
            else:
                del self.cache[command_id]
        return None
    
    def set(self, command_id: str, result: CommandResult):
        """Cache command result"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[command_id] = (result, datetime.now())
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hit_rate": 0.0  # Would need to track hits/misses
        }
