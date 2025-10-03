"""
Command Processing Pipeline
Main pipeline for processing commands from parsing to execution
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import uuid
from pathlib import Path

from command_models import (
    Command, ParsedCommand, CommandResult, CommandStatus, CommandPriority,
    CommandQueue, CommandValidator, CommandMetrics, CommandCache,
    IntentType, ParameterType
)
from intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class CommandProcessor:
    """Main command processor"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.command_queue = CommandQueue()
        self.metrics = CommandMetrics()
        self.cache = CommandCache()
        self.processing_commands: Dict[str, ParsedCommand] = {}
        self.is_running = False
        self.max_concurrent = 10
        self.timeout_seconds = 30
        
        # Service clients (would be injected in real implementation)
        self.service_clients = {}
        
        # Background tasks
        self._queue_processor_task = None
        self._timeout_monitor_task = None
        self._metrics_cleanup_task = None
    
    async def start(self):
        """Start the command processor"""
        self.is_running = True
        
        # Start background tasks
        self._queue_processor_task = asyncio.create_task(self._process_queue())
        self._timeout_monitor_task = asyncio.create_task(self._monitor_timeouts())
        self._metrics_cleanup_task = asyncio.create_task(self._cleanup_metrics())
        
        logger.info("Command processor started")
    
    async def stop(self):
        """Stop the command processor"""
        self.is_running = False
        
        # Cancel background tasks
        if self._queue_processor_task:
            self._queue_processor_task.cancel()
        if self._timeout_monitor_task:
            self._timeout_monitor_task.cancel()
        if self._metrics_cleanup_task:
            self._metrics_cleanup_task.cancel()
        
        logger.info("Command processor stopped")
    
    async def process_command(self, command: Command) -> CommandResult:
        """Process a single command"""
        start_time = datetime.now()
        
        try:
            # Check cache first
            cached_result = self.cache.get(command.id)
            if cached_result:
                logger.debug(f"Returning cached result for command {command.id}")
                return cached_result
            
            # Validate command
            is_valid, errors = CommandValidator.validate_command_text(command.text)
            if not is_valid:
                return CommandResult(
                    command_id=command.id,
                    success=False,
                    response=f"Invalid command: {', '.join(errors)}",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error_details={"type": "validation_error", "errors": errors}
                )
            
            # Parse command
            parsed_command = await self._parse_command(command)
            
            # Execute command
            result = await self._execute_command(parsed_command)
            
            # Cache successful results
            if result.success:
                self.cache.set(command.id, result)
            
            # Record metrics
            self.metrics.record_command(parsed_command, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing command {command.id}: {e}")
            return CommandResult(
                command_id=command.id,
                success=False,
                response=f"Error processing command: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds(),
                error_details={"type": "processing_error", "error": str(e)}
            )
    
    async def queue_command(self, command: Command) -> str:
        """Queue a command for processing"""
        if self.command_queue.add_command(command):
            logger.info(f"Command {command.id} queued with priority {command.priority}")
            return command.id
        else:
            raise Exception("Command queue is full")
    
    async def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a command"""
        # Check if command is being processed
        if command_id in self.processing_commands:
            parsed_command = self.processing_commands[command_id]
            return {
                "id": command_id,
                "status": parsed_command.status,
                "intent": parsed_command.intent,
                "confidence": parsed_command.confidence,
                "started_at": parsed_command.started_at.isoformat() if parsed_command.started_at else None,
                "processing_time": parsed_command.processing_time
            }
        
        # Check if command is in queue
        for queued_command in self.command_queue.commands:
            if queued_command.id == command_id:
                return {
                    "id": command_id,
                    "status": queued_command.status,
                    "queue_position": self.command_queue.commands.index(queued_command) + 1
                }
        
        # Check cache for completed commands
        cached_result = self.cache.get(command_id)
        if cached_result:
            return {
                "id": command_id,
                "status": "completed",
                "success": cached_result.success,
                "completed_at": cached_result.timestamp.isoformat()
            }
        
        return None
    
    async def cancel_command(self, command_id: str) -> bool:
        """Cancel a queued or processing command"""
        # Remove from queue
        if self.command_queue.remove_command(command_id):
            logger.info(f"Command {command_id} removed from queue")
            return True
        
        # Cancel processing command
        if command_id in self.processing_commands:
            parsed_command = self.processing_commands[command_id]
            parsed_command.status = CommandStatus.CANCELLED
            del self.processing_commands[command_id]
            logger.info(f"Command {command_id} cancelled")
            return True
        
        return False
    
    async def _parse_command(self, command: Command) -> ParsedCommand:
        """Parse and validate a command"""
        start_time = datetime.now()
        
        try:
            # Classify intent
            intent, confidence, alternatives = await self.intent_classifier.classify_intent(
                command.text, command.context
            )
            
            # Extract parameters
            parameters = await self.intent_classifier.extract_parameters(
                command.text, intent, command.context
            )
            
            # Validate parameters
            schema = self.intent_classifier.get_intent_schema(intent)
            validated_parameters = {}
            validation_errors = []
            
            if schema:
                is_valid, validated_params, errors = CommandValidator.validate_parameters(
                    parameters, schema.parameters
                )
                validated_parameters = validated_params
                validation_errors = errors
            
            # Create parsed command
            parsed_command = ParsedCommand(
                **command.dict(),
                intent=intent,
                confidence=confidence,
                parameters=parameters,
                validated_parameters=validated_parameters,
                alternatives=alternatives,
                processing_time=(datetime.now() - start_time).total_seconds(),
                errors=validation_errors
            )
            
            return parsed_command
            
        except Exception as e:
            logger.error(f"Error parsing command {command.id}: {e}")
            # Return parsed command with error
            return ParsedCommand(
                **command.dict(),
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                parameters={},
                validated_parameters={},
                alternatives=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                errors=[str(e)]
            )
    
    async def _execute_command(self, parsed_command: ParsedCommand) -> CommandResult:
        """Execute a parsed command"""
        start_time = datetime.now()
        
        try:
            # Update status
            parsed_command.status = CommandStatus.PROCESSING
            parsed_command.started_at = datetime.now()
            self.processing_commands[parsed_command.id] = parsed_command
            
            # Get service and tool information
            schema = self.intent_classifier.get_intent_schema(parsed_command.intent)
            if not schema:
                raise Exception(f"No schema found for intent: {parsed_command.intent}")
            
            service_name = schema.service
            tool_name = schema.tool
            
            # Call service
            result = await self._call_service(service_name, tool_name, parsed_command)
            
            # Update status
            parsed_command.status = CommandStatus.COMPLETED
            parsed_command.completed_at = datetime.now()
            
            # Remove from processing
            if parsed_command.id in self.processing_commands:
                del self.processing_commands[parsed_command.id]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CommandResult(
                command_id=parsed_command.id,
                success=result.get("success", True),
                response=result.get("response", "Command executed successfully"),
                data=result.get("data", {}),
                suggestions=result.get("suggestions", []),
                execution_time=execution_time,
                service_used=service_name
            )
            
        except Exception as e:
            logger.error(f"Error executing command {parsed_command.id}: {e}")
            
            # Update status
            parsed_command.status = CommandStatus.FAILED
            parsed_command.completed_at = datetime.now()
            
            # Remove from processing
            if parsed_command.id in self.processing_commands:
                del self.processing_commands[parsed_command.id]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CommandResult(
                command_id=parsed_command.id,
                success=False,
                response=f"Command execution failed: {str(e)}",
                execution_time=execution_time,
                error_details={"type": "execution_error", "error": str(e)}
            )
    
    async def _call_service(self, service_name: str, tool_name: str, parsed_command: ParsedCommand) -> Dict[str, Any]:
        """Call a service to execute the command"""
        try:
            # In a real implementation, this would call the actual service
            # For now, we'll simulate the service call
            
            # Simulate different responses based on intent
            if parsed_command.intent == IntentType.AUDIO_CONTROL:
                action = parsed_command.validated_parameters.get("action", "play")
                target = parsed_command.validated_parameters.get("target", "music")
                
                return {
                    "success": True,
                    "response": f"Audio control: {action} {target}",
                    "data": {
                        "action": action,
                        "target": target,
                        "service": service_name
                    },
                    "suggestions": [
                        "adjust volume",
                        "pause music",
                        "next song"
                    ]
                }
            
            elif parsed_command.intent == IntentType.SYSTEM_CONTROL:
                action = parsed_command.validated_parameters.get("action", "open")
                target = parsed_command.validated_parameters.get("target", "application")
                
                return {
                    "success": True,
                    "response": f"System control: {action} {target}",
                    "data": {
                        "action": action,
                        "target": target,
                        "service": service_name
                    },
                    "suggestions": [
                        "close application",
                        "open another app",
                        "check running processes"
                    ]
                }
            
            elif parsed_command.intent == IntentType.SMART_HOME:
                device_type = parsed_command.validated_parameters.get("device_type", "lights")
                action = parsed_command.validated_parameters.get("action", "on")
                location = parsed_command.validated_parameters.get("location", "room")
                
                return {
                    "success": True,
                    "response": f"Smart home: {action} {device_type} in {location}",
                    "data": {
                        "device_type": device_type,
                        "action": action,
                        "location": location,
                        "service": service_name
                    },
                    "suggestions": [
                        "dim lights",
                        "set temperature",
                        "lock doors"
                    ]
                }
            
            elif parsed_command.intent == IntentType.INFORMATION:
                query = parsed_command.validated_parameters.get("query", parsed_command.text)
                query_type = parsed_command.validated_parameters.get("type", "general")
                
                return {
                    "success": True,
                    "response": f"Information: {query_type} query about '{query}'",
                    "data": {
                        "query": query,
                        "type": query_type,
                        "service": service_name
                    },
                    "suggestions": [
                        "ask another question",
                        "get weather",
                        "check time"
                    ]
                }
            
            else:
                return {
                    "success": True,
                    "response": f"Command executed: {parsed_command.text}",
                    "data": {
                        "intent": parsed_command.intent,
                        "parameters": parsed_command.validated_parameters,
                        "service": service_name
                    },
                    "suggestions": []
                }
                
        except Exception as e:
            logger.error(f"Error calling service {service_name}: {e}")
            raise
    
    async def _process_queue(self):
        """Process commands from the queue"""
        while self.is_running:
            try:
                # Check if we can process more commands
                if len(self.processing_commands) >= self.max_concurrent:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get next command from queue
                command = self.command_queue.get_next_command()
                if not command:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process command asynchronously
                asyncio.create_task(self.process_command(command))
                
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_timeouts(self):
        """Monitor for command timeouts"""
        while self.is_running:
            try:
                current_time = datetime.now()
                timed_out_commands = []
                
                for command_id, parsed_command in self.processing_commands.items():
                    if parsed_command.started_at:
                        elapsed = (current_time - parsed_command.started_at).total_seconds()
                        if elapsed > parsed_command.timeout:
                            timed_out_commands.append(command_id)
                
                # Handle timed out commands
                for command_id in timed_out_commands:
                    parsed_command = self.processing_commands[command_id]
                    parsed_command.status = CommandStatus.TIMEOUT
                    parsed_command.completed_at = current_time
                    
                    logger.warning(f"Command {command_id} timed out after {parsed_command.timeout} seconds")
                    
                    # Remove from processing
                    del self.processing_commands[command_id]
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}")
                await asyncio.sleep(1)
    
    async def _cleanup_metrics(self):
        """Periodic cleanup of metrics and cache"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                
                # Reset metrics if they get too large
                if self.metrics.total_commands > 10000:
                    self.metrics.reset_metrics()
                    logger.info("Metrics reset due to size")
                
                # Clear old cache entries
                self.cache.clear()
                logger.info("Cache cleared")
                
            except Exception as e:
                logger.error(f"Error in metrics cleanup: {e}")
                await asyncio.sleep(3600)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get command queue status"""
        return {
            "queue": self.command_queue.get_queue_status(),
            "processing": {
                "active_commands": len(self.processing_commands),
                "max_concurrent": self.max_concurrent,
                "command_ids": list(self.processing_commands.keys())
            },
            "metrics": self.metrics.get_metrics(),
            "cache": self.cache.get_stats()
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "metrics": self.metrics.get_metrics(),
            "queue_status": self.command_queue.get_queue_status(),
            "cache_stats": self.cache.get_stats(),
            "active_commands": len(self.processing_commands),
            "is_running": self.is_running
        }
