# AI-SERVIS Command Processing Pipeline

The Command Processing Pipeline is the core component responsible for parsing, validating, classifying, and executing natural language commands in the AI-SERVIS system.

## Features

### 🧠 **Intent Classification**
- **Multi-method Classification**: Combines keyword matching, machine learning, and pattern recognition
- **Confidence Scoring**: Provides confidence scores for intent classification
- **Alternative Intents**: Returns alternative intent suggestions
- **Extensible Schemas**: Easy to add new intents and parameters
- **Training Support**: Machine learning model training with custom data

### 📝 **Command Parsing & Validation**
- **Text Preprocessing**: Cleans and normalizes command text
- **Parameter Extraction**: Automatically extracts parameters from natural language
- **Validation**: Validates parameters against defined schemas
- **Error Handling**: Comprehensive error detection and reporting
- **Security**: Validates commands for potentially dangerous operations

### ⚡ **Command Execution Pipeline**
- **Priority Queue**: Commands processed based on priority levels
- **Concurrent Processing**: Multiple commands processed simultaneously
- **Timeout Management**: Automatic timeout handling for long-running commands
- **Service Integration**: Seamless integration with AI-SERVIS services
- **Result Caching**: Caches successful results for improved performance

### 🎯 **Response Formatting**
- **Interface-Specific**: Tailored responses for voice, text, web, and mobile interfaces
- **Rich Formatting**: Supports rich data, suggestions, and metadata
- **Template System**: Configurable response templates
- **Length Optimization**: Automatically truncates responses based on interface capabilities

## Architecture

### Core Components

1. **Command Models**: Data structures for commands, results, and schemas
2. **Intent Classifier**: Multi-method intent classification system
3. **Command Pipeline**: Main processing pipeline with queue management
4. **Response Formatter**: Interface-specific response formatting
5. **Parameter Extractor**: Natural language parameter extraction
6. **Command Validator**: Security and validation utilities

### Supported Intents

- **Audio Control**: Music playback, volume control, device switching
- **System Control**: Application management, process control
- **Smart Home**: Device control, automation, security
- **Communication**: Messaging, calling, notifications
- **Navigation**: Directions, routing, location services
- **Information**: Question answering, weather, time
- **File Operations**: Download, upload, file management
- **Hardware Control**: GPIO, sensors, embedded devices

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# For machine learning features
pip install scikit-learn numpy pandas

# For natural language processing
pip install nltk spacy textblob
```

### Configuration

Set environment variables for configuration:

```bash
# Processing Configuration
export MAX_CONCURRENT_COMMANDS=10
export COMMAND_TIMEOUT=30
export ENABLE_CACHING=true
export CACHE_TTL=3600

# Model Configuration
export MODEL_PATH=models/
export TRAINING_DATA_PATH=data/training/

# Logging
export LOG_LEVEL=INFO
```

## Usage

### Basic Command Processing

```python
from command_processor import CommandProcessingService

# Create service
service = CommandProcessingService()
await service.start()

# Process a command
result = await service.process_command(
    command_text="play jazz music",
    user_id="user123",
    interface_type="voice"
)

print(result["response"])  # "Audio control: play jazz music"
```

### Intent Classification

```python
# Classify intent
intent_result = await service.classify_intent("turn on the lights")
print(intent_result["intent"])  # "smart_home"
print(intent_result["confidence"])  # 0.95
```

### Parameter Extraction

```python
# Extract parameters
parameters = await service.extract_parameters(
    "set volume to 75",
    "audio_control"
)
print(parameters)  # {"action": "volume", "level": 75}
```

### Command Queuing

```python
# Queue command for processing
command_id = await service.queue_command(
    command_text="download file from URL",
    priority=CommandPriority.HIGH
)

# Check status
status = await service.get_command_status(command_id)
print(status["status"])  # "processing"
```

## API Reference

### Command Processing Service

#### `process_command(command_text, user_id, session_id, interface_type, priority, context)`
Process a command and return formatted response.

**Parameters:**
- `command_text` (str): The command text to process
- `user_id` (str, optional): User identifier
- `session_id` (str, optional): Session identifier
- `interface_type` (str): Interface type ("voice", "text", "web", "mobile")
- `priority` (CommandPriority): Command priority level
- `context` (dict, optional): Additional context

**Returns:** Dict with formatted response

#### `queue_command(command_text, user_id, session_id, interface_type, priority, context)`
Queue a command for asynchronous processing.

**Returns:** Command ID for tracking

#### `get_command_status(command_id)`
Get the status of a queued or processing command.

**Returns:** Status information or None if not found

#### `cancel_command(command_id)`
Cancel a queued or processing command.

**Returns:** Boolean indicating success

### Intent Classification

#### `classify_intent(text, context)`
Classify the intent of a command text.

**Returns:** Dict with intent, confidence, and alternatives

#### `extract_parameters(text, intent, context)`
Extract parameters from text for a specific intent.

**Returns:** Dict with extracted parameters

### Model Training

#### `train_model(training_data)`
Train the intent classification model.

**Parameters:**
- `training_data` (List[Dict]): Training examples with "text" and "intent" keys

## Command Examples

### Audio Control
```
"play music" → {"intent": "audio_control", "action": "play"}
"turn up volume" → {"intent": "audio_control", "action": "volume", "level": "up"}
"switch to headphones" → {"intent": "audio_control", "action": "switch", "device": "headphones"}
```

### Smart Home
```
"turn on lights" → {"intent": "smart_home", "device_type": "lights", "action": "on"}
"dim bedroom lights" → {"intent": "smart_home", "device_type": "lights", "action": "dim", "location": "bedroom"}
"set temperature to 72" → {"intent": "smart_home", "device_type": "temperature", "action": "set", "value": 72}
```

### System Control
```
"open browser" → {"intent": "system_control", "action": "open", "target": "browser"}
"close all windows" → {"intent": "system_control", "action": "close", "target": "all windows"}
"run python script" → {"intent": "system_control", "action": "run", "target": "python script"}
```

### Communication
```
"send message to John" → {"intent": "communication", "action": "send", "recipient": "John"}
"call mom" → {"intent": "communication", "action": "call", "recipient": "mom"}
"text my friend" → {"intent": "communication", "action": "message", "recipient": "my friend"}
```

## Response Formatting

### Voice Interface
```json
{
  "success": true,
  "response": "Playing jazz music",
  "formatted_response": "Playing jazz music",
  "suggestions": ["You can also say: adjust volume", "You can also say: pause music"],
  "voice_metadata": {
    "speech_rate": "normal",
    "audio_cue": "music_start"
  }
}
```

### Web Interface
```json
{
  "success": true,
  "response": "✅ Playing jazz music",
  "formatted_response": "✅ Playing jazz music",
  "suggestions": ["Try these commands: adjust volume", "Try these commands: pause music"],
  "metadata": {
    "service_used": "ai-audio-assistant",
    "execution_time": 0.15
  },
  "action_buttons": [
    {"text": "adjust volume", "action": "quick_command", "command": "adjust volume"}
  ]
}
```

### Mobile Interface
```json
{
  "success": true,
  "response": "Playing jazz music",
  "formatted_response": "Playing jazz music",
  "quick_actions": [
    {"title": "adjust volume", "action": "command", "value": "adjust volume"}
  ],
  "push_notification": {
    "title": "AI-SERVIS",
    "body": "Playing jazz music"
  }
}
```

## Training Data Format

### Intent Classification Training
```json
[
  {
    "text": "play music",
    "intent": "audio_control"
  },
  {
    "text": "turn on lights",
    "intent": "smart_home"
  },
  {
    "text": "open browser",
    "intent": "system_control"
  }
]
```

### Parameter Extraction Training
```json
[
  {
    "text": "set volume to 75",
    "intent": "audio_control",
    "parameters": {
      "action": "volume",
      "level": 75
    }
  }
]
```

## Monitoring & Statistics

### Processing Statistics
```python
stats = await service.get_processing_stats()
print(stats)
```

**Output:**
```json
{
  "service_stats": {
    "total_commands": 150,
    "successful_commands": 142,
    "failed_commands": 8,
    "uptime": 3600.5
  },
  "processor_stats": {
    "metrics": {
      "success_rate": 0.947,
      "average_response_time": 0.25
    },
    "queue_status": {
      "total_commands": 5,
      "processing_limit": 10
    }
  }
}
```

### Intent Distribution
```json
{
  "intent_distribution": {
    "audio_control": 45,
    "smart_home": 32,
    "system_control": 28,
    "communication": 15,
    "information": 20,
    "navigation": 8,
    "file_operation": 2
  }
}
```

## Performance Optimization

### Caching
- **Result Caching**: Successful results cached for 1 hour by default
- **Intent Caching**: Frequently used intents cached for faster classification
- **Parameter Caching**: Common parameter patterns cached

### Concurrency
- **Queue Processing**: Commands processed in priority order
- **Concurrent Execution**: Multiple commands processed simultaneously
- **Timeout Management**: Automatic timeout handling prevents hanging

### Memory Management
- **Metrics Cleanup**: Automatic cleanup of old metrics data
- **Cache Management**: LRU cache with configurable size limits
- **Model Optimization**: Efficient model storage and loading

## Security

### Command Validation
- **Dangerous Command Detection**: Identifies potentially harmful commands
- **Input Sanitization**: Cleans and validates all input
- **Parameter Validation**: Strict parameter type and range validation
- **Rate Limiting**: Prevents command flooding

### Error Handling
- **Graceful Degradation**: System continues operating even with errors
- **Error Logging**: Comprehensive error logging and monitoring
- **Fallback Responses**: Default responses for unknown commands

## Development

### Adding New Intents

1. **Define Intent Schema**:
```python
new_intent = IntentSchema(
    intent=IntentType.NEW_INTENT,
    keywords=["keyword1", "keyword2"],
    parameters=[
        ParameterSchema(
            name="param1",
            type=ParameterType.STRING,
            required=True
        )
    ],
    service="new-service",
    tool="new_tool"
)
```

2. **Add to Classifier**:
```python
self.intent_schemas[IntentType.NEW_INTENT] = new_intent
```

3. **Implement Parameter Extraction**:
```python
def _extract_new_intent_parameters(self, text: str) -> Dict[str, Any]:
    # Implementation here
    pass
```

### Testing

```bash
# Run tests
pytest tests/

# Test specific components
pytest tests/test_intent_classifier.py
pytest tests/test_command_pipeline.py
pytest tests/test_response_formatter.py
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --verbose
```

## Troubleshooting

### Common Issues

1. **Low Intent Confidence**: Add more training data or keywords
2. **Parameter Extraction Errors**: Check parameter schemas and extraction logic
3. **Slow Processing**: Increase concurrent processing limit or optimize models
4. **Memory Issues**: Reduce cache size or enable metrics cleanup

### Performance Tuning

- **Model Size**: Use smaller models for faster classification
- **Cache Size**: Adjust cache size based on available memory
- **Concurrency**: Tune concurrent processing based on system resources
- **Timeout**: Adjust timeouts based on expected command complexity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## License

This module is part of the AI-SERVIS Universal project and follows the same license terms.
