"""
AI-SERVIS Command Processing Pipeline Main Module
Main entry point for the command processing system
"""
import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from command_models import (
    Command, CommandStatus, CommandPriority, CommandResult,
    CommandValidator, IntentType
)
from command_pipeline import CommandProcessor
from response_formatter import ResponseFormatter
from intent_classifier import IntentClassifier

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CommandProcessingService:
    """Main command processing service"""
    
    def __init__(self):
        self.command_processor = CommandProcessor()
        self.response_formatter = ResponseFormatter()
        self.intent_classifier = IntentClassifier()
        self.is_running = False
        
        # Configuration
        self.config = self._load_config()
        
        # Statistics
        self.stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "start_time": None
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment or defaults"""
        return {
            "max_concurrent_commands": int(os.getenv("MAX_CONCURRENT_COMMANDS", "10")),
            "command_timeout": int(os.getenv("COMMAND_TIMEOUT", "30")),
            "cache_ttl": int(os.getenv("CACHE_TTL", "3600")),
            "enable_caching": os.getenv("ENABLE_CACHING", "true").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "model_path": os.getenv("MODEL_PATH", "models/"),
            "training_data_path": os.getenv("TRAINING_DATA_PATH", "data/training/")
        }
    
    async def start(self):
        """Start the command processing service"""
        try:
            logger.info("Starting AI-SERVIS Command Processing Service")
            
            # Start command processor
            await self.command_processor.start()
            
            # Load training data if available
            await self._load_training_data()
            
            self.is_running = True
            self.stats["start_time"] = datetime.now()
            
            logger.info("Command Processing Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Command Processing Service: {e}")
            raise
    
    async def stop(self):
        """Stop the command processing service"""
        try:
            logger.info("Stopping Command Processing Service")
            
            self.is_running = False
            
            # Stop command processor
            await self.command_processor.stop()
            
            logger.info("Command Processing Service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Command Processing Service: {e}")
    
    async def process_command(self, command_text: str, user_id: Optional[str] = None, 
                            session_id: Optional[str] = None, interface_type: str = "text",
                            priority: CommandPriority = CommandPriority.NORMAL,
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a command and return formatted response"""
        try:
            # Create command object
            command = Command(
                text=command_text,
                user_id=user_id,
                session_id=session_id,
                interface_type=interface_type,
                priority=priority,
                context=context or {}
            )
            
            # Process command
            result = await self.command_processor.process_command(command)
            
            # Format response for interface
            formatted_response = await self.response_formatter.format_response(result, interface_type)
            
            # Update statistics
            self._update_stats(result)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                "success": False,
                "response": f"Error processing command: {str(e)}",
                "interface_type": interface_type,
                "timestamp": datetime.now().isoformat()
            }
    
    async def queue_command(self, command_text: str, user_id: Optional[str] = None,
                          session_id: Optional[str] = None, interface_type: str = "text",
                          priority: CommandPriority = CommandPriority.NORMAL,
                          context: Optional[Dict[str, Any]] = None) -> str:
        """Queue a command for processing"""
        try:
            # Create command object
            command = Command(
                text=command_text,
                user_id=user_id,
                session_id=session_id,
                interface_type=interface_type,
                priority=priority,
                context=context or {}
            )
            
            # Queue command
            command_id = await self.command_processor.queue_command(command)
            
            return command_id
            
        except Exception as e:
            logger.error(f"Error queuing command: {e}")
            raise
    
    async def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a command"""
        return await self.command_processor.get_command_status(command_id)
    
    async def cancel_command(self, command_id: str) -> bool:
        """Cancel a command"""
        return await self.command_processor.cancel_command(command_id)
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        processor_stats = self.command_processor.get_processing_stats()
        
        return {
            "service_stats": self.stats,
            "processor_stats": processor_stats,
            "uptime": (datetime.now() - self.stats["start_time"]).total_seconds() if self.stats["start_time"] else 0,
            "is_running": self.is_running
        }
    
    async def get_intent_schemas(self) -> Dict[str, Any]:
        """Get all intent schemas"""
        schemas = self.intent_classifier.get_all_schemas()
        return {intent.value: schema.dict() for intent, schema in schemas.items()}
    
    async def train_model(self, training_data: List[Dict[str, Any]]):
        """Train the intent classification model"""
        try:
            # Convert training data to required format
            formatted_data = []
            for item in training_data:
                text = item.get("text", "")
                intent = item.get("intent", "")
                if text and intent:
                    formatted_data.append((text, intent))
            
            # Train model
            self.intent_classifier.train_model(formatted_data)
            
            logger.info(f"Model trained with {len(formatted_data)} examples")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    async def classify_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify intent for a given text"""
        try:
            intent, confidence, alternatives = await self.intent_classifier.classify_intent(
                text, context or {}
            )
            
            return {
                "intent": intent.value,
                "confidence": confidence,
                "alternatives": [{"intent": alt[0], "confidence": alt[1]} for alt in alternatives]
            }
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "alternatives": []
            }
    
    async def extract_parameters(self, text: str, intent: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract parameters from text for a given intent"""
        try:
            intent_type = IntentType(intent)
            parameters = await self.intent_classifier.extract_parameters(
                text, intent_type, context or {}
            )
            
            return parameters
            
        except Exception as e:
            logger.error(f"Error extracting parameters: {e}")
            return {}
    
    def _update_stats(self, result: CommandResult):
        """Update service statistics"""
        self.stats["total_commands"] += 1
        
        if result.success:
            self.stats["successful_commands"] += 1
        else:
            self.stats["failed_commands"] += 1
    
    async def _load_training_data(self):
        """Load training data if available"""
        try:
            training_data_path = Path(self.config["training_data_path"])
            if training_data_path.exists():
                training_files = list(training_data_path.glob("*.json"))
                
                for file_path in training_files:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    if isinstance(data, list):
                        # Convert to training format
                        training_data = []
                        for item in data:
                            if "text" in item and "intent" in item:
                                training_data.append((item["text"], item["intent"]))
                        
                        if training_data:
                            self.intent_classifier.train_model(training_data)
                            logger.info(f"Loaded training data from {file_path}")
                
        except Exception as e:
            logger.warning(f"Could not load training data: {e}")


# Example usage and testing
async def main():
    """Main entry point for testing"""
    logger.info("Starting AI-SERVIS Command Processing Service")
    
    # Create and start service
    service = CommandProcessingService()
    
    try:
        await service.start()
        
        # Test commands
        test_commands = [
            "play music",
            "turn on the lights",
            "what's the weather",
            "open browser",
            "send message to John"
        ]
        
        logger.info("Testing command processing...")
        
        for command_text in test_commands:
            logger.info(f"Processing: {command_text}")
            
            # Process command
            result = await service.process_command(
                command_text=command_text,
                user_id="test_user",
                interface_type="text"
            )
            
            logger.info(f"Result: {result['response']}")
            
            # Classify intent
            intent_result = await service.classify_intent(command_text)
            logger.info(f"Intent: {intent_result['intent']} (confidence: {intent_result['confidence']:.2f})")
            
            print("-" * 50)
        
        # Get statistics
        stats = await service.get_processing_stats()
        logger.info(f"Processing statistics: {stats}")
        
        # Keep running for interactive testing
        logger.info("Service is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
