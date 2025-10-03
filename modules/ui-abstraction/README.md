# AI-SERVIS UI Abstraction Module

The UI Abstraction module provides a unified interface layer for AI-SERVIS, supporting multiple user interface types including voice, text, web, and mobile interfaces.

## Features

### 🎤 Voice Interface
- **WebRTC Support**: Real-time audio communication
- **Voice Activity Detection**: Automatic speech detection
- **Audio Processing**: Noise reduction and format conversion
- **WebSocket Communication**: Low-latency bidirectional communication
- **Configurable Audio Settings**: Sample rate, channels, and format options

### 💬 Text Interface
- **CLI Support**: Command-line interface for direct interaction
- **Web-based Chat**: HTML interface with real-time messaging
- **WebSocket Support**: Real-time text communication
- **HTTP API**: RESTful API for programmatic access
- **Multi-session Support**: Multiple concurrent text sessions

### 🌐 Web Interface
- **Modern UI**: Responsive web interface with Material Design
- **Socket.IO Integration**: Real-time bidirectional communication
- **Interactive Chat**: Rich chat interface with suggestions
- **Connection Management**: Real-time connection monitoring
- **Mobile Responsive**: Works on desktop and mobile browsers

### 📱 Mobile Interface
- **REST API**: Full REST API for mobile app integration
- **WebSocket Support**: Real-time communication for mobile apps
- **Push Notifications**: FCM and APNS support for notifications
- **Device Management**: Device registration and management
- **Authentication**: Secure device authentication
- **Multi-platform**: Support for iOS and Android

## Architecture

### Core Components

1. **UI Manager**: Central coordinator for all UI interfaces
2. **UI Adapters**: Individual interface implementations
3. **Message System**: Unified message handling across interfaces
4. **Connection Management**: Session and connection tracking
5. **Orchestrator Integration**: Communication with core orchestrator

### Message Types

- **Command Messages**: User commands from interfaces
- **Response Messages**: Orchestrator responses
- **Status Messages**: System status updates
- **Error Messages**: Error notifications
- **Notification Messages**: General notifications
- **Heartbeat Messages**: Connection health monitoring

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# For voice interface (optional)
pip install numpy scipy librosa

# For web interface
pip install python-socketio eventlet

# For mobile push notifications (optional)
pip install firebase-admin pyapns
```

### Configuration

Set environment variables for configuration:

```bash
# Voice Interface
export VOICE_INTERFACE_ENABLED=true
export VOICE_INTERFACE_HOST=localhost
export VOICE_INTERFACE_PORT=8081

# Text Interface
export TEXT_INTERFACE_ENABLED=true
export TEXT_INTERFACE_HOST=localhost
export TEXT_INTERFACE_PORT=8082
export TEXT_ENABLE_CLI=true

# Web Interface
export WEB_INTERFACE_ENABLED=true
export WEB_INTERFACE_HOST=localhost
export WEB_INTERFACE_PORT=8083

# Mobile Interface
export MOBILE_INTERFACE_ENABLED=true
export MOBILE_INTERFACE_HOST=localhost
export MOBILE_INTERFACE_PORT=8084

# Orchestrator Connection
export ORCHESTRATOR_HOST=localhost
export ORCHESTRATOR_PORT=8080
```

## Usage

### Starting the UI Abstraction Manager

```bash
# Start all interfaces
python main.py

# Or start with specific configuration
VOICE_INTERFACE_ENABLED=false python main.py
```

### Voice Interface

Connect to the voice interface via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8081');

// Send audio data
ws.send(JSON.stringify({
    type: 'audio_data',
    audio_data: base64AudioData
}));

// Send voice command
ws.send(JSON.stringify({
    type: 'voice_command',
    command: 'play music',
    user_id: 'user123'
}));
```

### Text Interface

#### CLI Usage
```bash
# Start CLI interface
python main.py

# Commands
AI-SERVIS> play music
AI-SERVIS> turn on lights
AI-SERVIS> what's the weather
AI-SERVIS> exit
```

#### Web Interface
Open browser to `http://localhost:8082` for web-based text interface.

#### HTTP API
```bash
# Send command via HTTP
curl -X POST http://localhost:8082/api/command \
  -H "Content-Type: application/json" \
  -d '{"command": "play music", "user_id": "user123"}'
```

### Web Interface

Open browser to `http://localhost:8083` for the modern web interface.

Features:
- Real-time chat interface
- Command suggestions
- Connection status monitoring
- Responsive design

### Mobile Interface

#### Device Registration
```bash
curl -X POST http://localhost:8084/api/mobile/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device123",
    "device_info": {
      "platform": "android",
      "version": "1.0.0",
      "user_id": "user123"
    }
  }'
```

#### Send Command
```bash
curl -X POST http://localhost:8084/api/mobile/command \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: device123" \
  -d '{
    "command": "play music",
    "context": {"location": "home"}
  }'
```

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8084/api/mobile/ws?device_id=device123');

ws.send(JSON.stringify({
    type: 'command',
    command: 'turn on lights',
    context: {}
}));
```

## API Reference

### Common Message Format

All interfaces use a unified message format:

```json
{
  "id": "unique_message_id",
  "type": "command|response|status|error|notification|heartbeat",
  "interface_type": "voice|text|web|mobile",
  "user_id": "user_identifier",
  "session_id": "session_identifier",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "command": "user command",
    "context": {},
    "metadata": {}
  }
}
```

### Response Format

```json
{
  "success": true,
  "response": "Command processed successfully",
  "data": {},
  "suggestions": ["next command", "alternative command"],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Development

### Adding New Interface Types

1. Create a new adapter class inheriting from `UIAdapter`
2. Implement required methods: `start()`, `stop()`, `send_message()`, `broadcast_message()`
3. Register the adapter in `main.py`
4. Add configuration options

### Custom Message Handlers

```python
def custom_message_handler(message: UIMessage, connection_id: str):
    # Handle custom message logic
    pass

# Register handler
adapter.add_message_handler(MessageType.COMMAND, custom_message_handler)
```

### Testing

```bash
# Run tests
pytest tests/

# Test specific interface
pytest tests/test_voice_interface.py
pytest tests/test_web_interface.py
```

## Monitoring

### Health Checks

All interfaces provide health check endpoints:

- Voice: `http://localhost:8081/health`
- Text: `http://localhost:8082/api/status`
- Web: `http://localhost:8083/api/status`
- Mobile: `http://localhost:8084/api/mobile/health`

### Statistics

Get interface statistics:

```bash
curl http://localhost:8082/api/status
curl http://localhost:8083/api/status
curl http://localhost:8084/api/mobile/status
```

## Security

### Authentication

- **Mobile Interface**: Device-based authentication with registration
- **Web Interface**: Session-based authentication
- **Voice/Text**: Optional user authentication

### Encryption

- **WebSocket**: TLS encryption for secure communication
- **Mobile**: Encrypted push notifications
- **API**: HTTPS support for all HTTP endpoints

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 8081-8084 are available
2. **WebSocket Connection**: Check firewall settings
3. **Audio Issues**: Verify audio device permissions
4. **Mobile Registration**: Ensure device ID is unique

### Logs

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Performance

- **Connection Limits**: Configure max connections per interface
- **Message Queuing**: Implement message queuing for high load
- **Resource Monitoring**: Monitor CPU and memory usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## License

This module is part of the AI-SERVIS Universal project and follows the same license terms.
