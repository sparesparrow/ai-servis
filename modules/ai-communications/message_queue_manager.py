"""
Message Queue and Delivery Manager
Handles message queuing, retry logic, and delivery tracking
"""
import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid

from messaging_service_abstraction import (
    Message, MessageType, MessageStatus, MessagePriority, MessagingServiceManager
)

logger = logging.getLogger(__name__)


class QueueStatus(Enum):
    """Queue status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class RetryStrategy(Enum):
    """Retry strategies"""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"


@dataclass
class QueueMessage:
    """Message in queue with retry information"""
    message: Message
    retry_count: int = 0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    next_retry_at: Optional[datetime] = None
    created_at: datetime = None
    last_attempt_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.next_retry_at is None:
            self.next_retry_at = datetime.now()


@dataclass
class DeliveryAttempt:
    """Delivery attempt record"""
    attempt_id: str
    message_id: str
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    response_time: Optional[float] = None


@dataclass
class QueueStatistics:
    """Queue statistics"""
    total_messages: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    pending_messages: int = 0
    retry_attempts: int = 0
    average_delivery_time: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class MessageQueueManager:
    """Manages message queuing and delivery"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Queue management
        self.queues: Dict[MessageType, List[QueueMessage]] = {}
        self.delivery_attempts: Dict[str, List[DeliveryAttempt]] = {}
        self.queue_status = QueueStatus.ACTIVE
        
        # Configuration
        self.max_queue_size = config.get("max_queue_size", 10000)
        self.default_max_retries = config.get("default_max_retries", 3)
        self.default_retry_strategy = RetryStrategy(config.get("default_retry_strategy", "exponential_backoff"))
        self.retry_intervals = config.get("retry_intervals", [1, 5, 15, 60])  # seconds
        self.batch_size = config.get("batch_size", 10)
        self.processing_interval = config.get("processing_interval", 1.0)  # seconds
        
        # Statistics
        self.statistics = QueueStatistics()
        
        # Callbacks
        self.delivery_callbacks: List[Callable[[Message, bool], None]] = []
        self.retry_callbacks: List[Callable[[Message, int], None]] = []
        
        # Control
        self.is_running = False
        self.processing_task: Optional[asyncio.Task] = None
        
        # Initialize queues
        self._initialize_queues()
    
    def _initialize_queues(self):
        """Initialize message queues for each service type"""
        for message_type in MessageType:
            self.queues[message_type] = []
    
    async def start(self):
        """Start the queue processing"""
        try:
            if self.is_running:
                return
            
            self.is_running = True
            self.queue_status = QueueStatus.ACTIVE
            self.processing_task = asyncio.create_task(self._processing_loop())
            
            logger.info("Message queue manager started")
            
        except Exception as e:
            logger.error(f"Error starting queue manager: {e}")
    
    async def stop(self):
        """Stop the queue processing"""
        try:
            self.is_running = False
            self.queue_status = QueueStatus.STOPPED
            
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Message queue manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping queue manager: {e}")
    
    async def pause(self):
        """Pause queue processing"""
        try:
            self.queue_status = QueueStatus.PAUSED
            logger.info("Message queue processing paused")
            
        except Exception as e:
            logger.error(f"Error pausing queue: {e}")
    
    async def resume(self):
        """Resume queue processing"""
        try:
            self.queue_status = QueueStatus.ACTIVE
            logger.info("Message queue processing resumed")
            
        except Exception as e:
            logger.error(f"Error resuming queue: {e}")
    
    async def enqueue_message(self, message: Message, max_retries: int = None, 
                            retry_strategy: RetryStrategy = None) -> bool:
        """Add message to queue"""
        try:
            if self.queue_status == QueueStatus.STOPPED:
                logger.warning("Queue is stopped, cannot enqueue message")
                return False
            
            # Check queue size
            queue = self.queues[message.type]
            if len(queue) >= self.max_queue_size:
                logger.warning(f"Queue for {message.type.value} is full, dropping message")
                return False
            
            # Create queue message
            queue_message = QueueMessage(
                message=message,
                max_retries=max_retries or self.default_max_retries,
                retry_strategy=retry_strategy or self.default_retry_strategy
            )
            
            # Add to appropriate queue based on priority
            if message.priority == MessagePriority.URGENT:
                queue.insert(0, queue_message)
            elif message.priority == MessagePriority.HIGH:
                # Insert after urgent messages
                urgent_count = sum(1 for qm in queue if qm.message.priority == MessagePriority.URGENT)
                queue.insert(urgent_count, queue_message)
            else:
                queue.append(queue_message)
            
            # Update statistics
            self.statistics.total_messages += 1
            self.statistics.pending_messages += 1
            self.statistics.last_updated = datetime.now()
            
            logger.info(f"Enqueued {message.type.value} message: {message.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueuing message: {e}")
            return False
    
    async def dequeue_message(self, message_type: MessageType) -> Optional[QueueMessage]:
        """Remove and return next message from queue"""
        try:
            queue = self.queues[message_type]
            if not queue:
                return None
            
            # Find next message ready for processing
            now = datetime.now()
            for i, queue_message in enumerate(queue):
                if queue_message.next_retry_at <= now:
                    return queue.pop(i)
            
            return None
            
        except Exception as e:
            logger.error(f"Error dequeuing message: {e}")
            return None
    
    async def process_message(self, queue_message: QueueMessage, 
                            service_manager: MessagingServiceManager) -> bool:
        """Process a single message"""
        try:
            message = queue_message.message
            start_time = time.time()
            
            # Record delivery attempt
            attempt_id = str(uuid.uuid4())
            attempt = DeliveryAttempt(
                attempt_id=attempt_id,
                message_id=message.id,
                timestamp=datetime.now(),
                success=False
            )
            
            # Send message
            success = await service_manager.send_message(message)
            
            # Record attempt result
            attempt.success = success
            attempt.response_time = time.time() - start_time
            
            if not success:
                attempt.error_message = message.error_message
            
            # Store attempt
            if message.id not in self.delivery_attempts:
                self.delivery_attempts[message.id] = []
            self.delivery_attempts[message.id].append(attempt)
            
            # Update statistics
            if success:
                self.statistics.successful_deliveries += 1
                self.statistics.pending_messages -= 1
            else:
                self.statistics.failed_deliveries += 1
                self.statistics.retry_attempts += 1
            
            # Update average delivery time
            if attempt.response_time:
                total_deliveries = self.statistics.successful_deliveries + self.statistics.failed_deliveries
                if total_deliveries > 0:
                    self.statistics.average_delivery_time = (
                        (self.statistics.average_delivery_time * (total_deliveries - 1) + attempt.response_time) 
                        / total_deliveries
                    )
            
            self.statistics.last_updated = datetime.now()
            
            # Notify callbacks
            await self._notify_delivery(message, success)
            
            if success:
                logger.info(f"Message {message.id} delivered successfully")
                return True
            else:
                logger.warning(f"Message {message.id} delivery failed: {message.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing message {queue_message.message.id}: {e}")
            return False
    
    async def handle_failed_message(self, queue_message: QueueMessage) -> bool:
        """Handle failed message delivery"""
        try:
            message = queue_message.message
            queue_message.retry_count += 1
            queue_message.last_attempt_at = datetime.now()
            
            # Check if we should retry
            if queue_message.retry_count >= queue_message.max_retries:
                # Max retries exceeded, mark as failed
                message.status = MessageStatus.FAILED
                self.statistics.pending_messages -= 1
                logger.error(f"Message {message.id} failed after {queue_message.retry_count} attempts")
                return False
            
            # Calculate next retry time
            next_retry_time = self._calculate_next_retry_time(queue_message)
            queue_message.next_retry_at = next_retry_time
            
            # Re-enqueue message
            queue = self.queues[message.type]
            queue.append(queue_message)
            
            # Notify retry callback
            await self._notify_retry(message, queue_message.retry_count)
            
            logger.info(f"Message {message.id} scheduled for retry {queue_message.retry_count} at {next_retry_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling failed message {queue_message.message.id}: {e}")
            return False
    
    def _calculate_next_retry_time(self, queue_message: QueueMessage) -> datetime:
        """Calculate next retry time based on strategy"""
        try:
            retry_count = queue_message.retry_count
            strategy = queue_message.retry_strategy
            
            if strategy == RetryStrategy.IMMEDIATE:
                delay = 0
            elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                delay = min(2 ** retry_count, 300)  # Max 5 minutes
            elif strategy == RetryStrategy.LINEAR_BACKOFF:
                delay = retry_count * 30  # 30 seconds per retry
            elif strategy == RetryStrategy.FIXED_INTERVAL:
                delay = 60  # 1 minute fixed
            else:
                delay = self.retry_intervals[min(retry_count, len(self.retry_intervals) - 1)]
            
            return datetime.now() + timedelta(seconds=delay)
            
        except Exception as e:
            logger.error(f"Error calculating retry time: {e}")
            return datetime.now() + timedelta(seconds=60)
    
    async def _processing_loop(self):
        """Main queue processing loop"""
        try:
            while self.is_running:
                if self.queue_status == QueueStatus.ACTIVE:
                    await self._process_queues()
                
                await asyncio.sleep(self.processing_interval)
                
        except asyncio.CancelledError:
            logger.info("Processing loop cancelled")
        except Exception as e:
            logger.error(f"Error in processing loop: {e}")
    
    async def _process_queues(self):
        """Process all message queues"""
        try:
            for message_type, queue in self.queues.items():
                if not queue:
                    continue
                
                # Process batch of messages
                processed_count = 0
                while processed_count < self.batch_size and queue:
                    queue_message = await self.dequeue_message(message_type)
                    if not queue_message:
                        break
                    
                    # Process message (this would need service_manager)
                    # For now, we'll simulate processing
                    success = await self._simulate_message_processing(queue_message)
                    
                    if not success:
                        await self.handle_failed_message(queue_message)
                    
                    processed_count += 1
                    
        except Exception as e:
            logger.error(f"Error processing queues: {e}")
    
    async def _simulate_message_processing(self, queue_message: QueueMessage) -> bool:
        """Simulate message processing (replace with actual service manager)"""
        try:
            # Simulate processing delay
            await asyncio.sleep(0.1)
            
            # Simulate success/failure (90% success rate)
            import random
            return random.random() < 0.9
            
        except Exception as e:
            logger.error(f"Error simulating message processing: {e}")
            return False
    
    async def get_queue_status(self, message_type: Optional[MessageType] = None) -> Dict[str, Any]:
        """Get queue status"""
        try:
            if message_type:
                queue = self.queues[message_type]
                return {
                    "message_type": message_type.value,
                    "queue_size": len(queue),
                    "pending_messages": len([qm for qm in queue if qm.next_retry_at <= datetime.now()]),
                    "retry_messages": len([qm for qm in queue if qm.retry_count > 0])
                }
            else:
                status = {}
                for msg_type, queue in self.queues.items():
                    status[msg_type.value] = {
                        "queue_size": len(queue),
                        "pending_messages": len([qm for qm in queue if qm.next_retry_at <= datetime.now()]),
                        "retry_messages": len([qm for qm in queue if qm.retry_count > 0])
                    }
                return status
                
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            return {
                "statistics": asdict(self.statistics),
                "queue_status": self.queue_status.value,
                "is_running": self.is_running,
                "total_queues": len(self.queues),
                "total_messages_in_queues": sum(len(queue) for queue in self.queues.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    async def get_message_history(self, message_id: str) -> List[DeliveryAttempt]:
        """Get delivery history for a message"""
        try:
            return self.delivery_attempts.get(message_id, [])
            
        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []
    
    async def clear_queue(self, message_type: MessageType) -> int:
        """Clear all messages from a queue"""
        try:
            queue = self.queues[message_type]
            cleared_count = len(queue)
            queue.clear()
            
            logger.info(f"Cleared {cleared_count} messages from {message_type.value} queue")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing queue {message_type.value}: {e}")
            return 0
    
    # Callback management
    def add_delivery_callback(self, callback: Callable[[Message, bool], None]):
        """Add delivery callback"""
        self.delivery_callbacks.append(callback)
    
    def add_retry_callback(self, callback: Callable[[Message, int], None]):
        """Add retry callback"""
        self.retry_callbacks.append(callback)
    
    async def _notify_delivery(self, message: Message, success: bool):
        """Notify delivery callbacks"""
        for callback in self.delivery_callbacks:
            try:
                callback(message, success)
            except Exception as e:
                logger.error(f"Error in delivery callback: {e}")
    
    async def _notify_retry(self, message: Message, retry_count: int):
        """Notify retry callbacks"""
        for callback in self.retry_callbacks:
            try:
                callback(message, retry_count)
            except Exception as e:
                logger.error(f"Error in retry callback: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.stop()
            logger.info("Message queue manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up queue manager: {e}")
