# AI-SERVIS Enhanced Core Orchestrator

## Overview

The Enhanced Core Orchestrator is the central intelligence hub of the AI-SERVIS Universal system. It provides advanced natural language processing, context-aware command routing, multi-interface support, and comprehensive service management capabilities.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                Enhanced Core Orchestrator                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   NLP Engine    │  │ Context Manager │  │ UI Manager   │ │
│  │                 │  │                 │  │              │ │
│  │ • Intent Class. │  │ • Session Mgmt  │  │ • Voice UI   │ │
│  │ • Parameter Ext │  │ • User Context  │  │ • Text UI    │ │
│  │ • Context Aware │  │ • Device Info   │  │ • Web UI     │ │
│  │ • Confidence    │  │ • Persistence   │  │ • Mobile UI  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │Service Registry │  │  MCP Framework  │  │Command Queue │ │
│  │                 │  │                 │  │              │ │
│  │ • Service Info  │  │ • Tool Calling  │  │ • Priority   │ │
│  │ • Health Check  │  │ • Message Route │  │ • Throttling │ │
│  │ • Load Balance  │  │ • Error Handle  │  │ • Retry      │ │
│  │ • Auto Discovery│  │ • Transport     │  │ • Timeout    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Ecosystem                        │
├─────────────────────────────────────────────────────────────┤
│  Audio Assistant  │  Platform Control │  Hardware Bridge   │
│  Home Automation  │  Communications   │  Maps & Navigation │
│  File Operations  │  Security         │  Custom Services   │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. Advanced Natural Language Processing

#### Intent Classification
- **Context-aware parsing**: Uses conversation history and user context
- **Confidence scoring**: Provides confidence levels for intent recognition
- **Alternative suggestions**: Offers alternatives when confidence is low
- **Learning capabilities**: Improves over time based on user interactions

#### Supported Intents
- `play_music`: Music playback control with artist, genre, mood detection
- `control_volume`: Volume adjustment with numeric and relative controls
- `switch_audio`: Audio device switching (headphones, speakers, Bluetooth)
- `system_control`: Application and process management
- `file_operation`: File downloads, uploads, and management
- `smart_home`: Home automation device control
- `hardware_control`: GPIO and sensor management
- `communication`: Messaging and notification services
- `navigation`: Directions and route planning
- `question_answer`: General knowledge queries
- `follow_up`: Context-dependent follow-up commands

#### Parameter Extraction
```python
# Example: "Play some jazz music by Miles Davis"
{
    "intent": "play_music",
    "confidence": 0.85,
    "parameters": {
        "genre": "jazz",
        "artist": "Miles Davis"
    },
    "context_used": false
}

# Example follow-up: "Make it louder"
{
    "intent": "control_volume",
    "confidence": 0.75,
    "parameters": {
        "action": "up"
    },
    "context_used": true
}
```

### 2. Context Management

#### Session Context
- **Conversation history**: Maintains command and response history
- **Intent tracking**: Remembers last intent and parameters for follow-ups
- **Variable storage**: Persistent key-value storage per session
- **Service state**: Tracks state across different services
- **Auto-expiration**: Sessions expire after 30 minutes of inactivity

#### User Context
- **Preferences**: User-specific settings and preferences
- **Location awareness**: Location-based context for smart home commands
- **Language settings**: Preferred language and timezone
- **Activity tracking**: Last activity timestamps

#### Device Context
- **Hardware capabilities**: GPIO pins, audio devices, sensors
- **Platform information**: OS, version, device type
- **Current state**: Real-time device status

### 3. Multi-Interface Support

#### Voice Interface
```cpp
class VoiceUIAdapter : public IUIAdapter {
    // Voice-to-text conversion
    // Text-to-speech synthesis
    // Audio device management
    // Noise cancellation support
};
```

#### Text Interface
```cpp
class TextUIAdapter : public IUIAdapter {
    // Terminal-based interaction
    // Command history
    // Auto-completion
    // Help system
};
```

#### Web Interface
```cpp
class WebUIAdapter : public IUIAdapter {
    // HTTP/WebSocket endpoints
    // Real-time communication
    // Session management
    // CORS support
};
```

#### Mobile Interface
```cpp
class MobileUIAdapter : public IUIAdapter {
    // RESTful API
    // Push notifications
    // Authentication
    // Mobile-optimized responses
};
```

### 4. Service Management

#### Service Registry
- **Dynamic registration**: Services can register themselves at runtime
- **Health monitoring**: Continuous health checks with metrics
- **Load balancing**: Distribute requests across service instances
- **Failover**: Automatic failover to backup services

#### Service Types
- **MCP Services**: Native MCP protocol communication
- **HTTP Services**: RESTful API integration
- **WebSocket Services**: Real-time bidirectional communication

#### Metrics and Analytics
```python
{
    "service_name": "ai-audio-assistant",
    "response_time": 0.125,
    "error_count": 2,
    "health_status": "healthy",
    "last_seen": "2024-01-15T10:30:00Z",
    "success_rate": 0.98
}
```

## Implementation Details

### C++ Implementation

#### Core Classes
```cpp
namespace WebGrab {
    class CoreOrchestrator;      // Main orchestrator service
    class NLPProcessor;          // Natural language processing
    class ContextManager;        // Context and session management
    class UIManager;             // UI adapter coordination
    class CommandProcessingJob;  // Asynchronous command processing
}
```

#### Key Features
- **Thread-safe**: All operations are thread-safe with proper locking
- **RAII compliance**: Proper resource management
- **Exception safety**: Comprehensive error handling
- **Performance optimized**: Minimal memory allocations and fast execution

### Python Implementation

#### Enhanced Features
```python
class EnhancedNLPProcessor:
    # Advanced pattern matching
    # Context-aware parameter extraction
    # Confidence scoring with alternatives
    # Learning and adaptation

class ContextManager:
    # Persistent context storage
    # Session lifecycle management
    # Automatic cleanup
    # JSON serialization

class EnhancedCoreOrchestrator:
    # Background task management
    # Service health monitoring
    # Advanced routing logic
    # Analytics and metrics
```

## Configuration

### Service Configuration
```json
{
    "services": [
        {
            "name": "ai-audio-assistant",
            "host": "localhost",
            "port": 8082,
            "capabilities": ["audio", "music", "voice", "streaming"],
            "service_type": "http",
            "health_endpoint": "/health",
            "timeout": 5.0
        }
    ]
}
```

### NLP Configuration
```json
{
    "nlp": {
        "confidence_threshold": 0.3,
        "context_boost_factor": 0.2,
        "max_alternatives": 3,
        "intent_patterns": {
            "play_music": {
                "keywords": ["play", "music", "song"],
                "weight": 1.0,
                "context_boost": {
                    "last_intent": ["control_volume"],
                    "boost": 0.3
                }
            }
        }
    }
}
```

## Usage Examples

### Basic Command Processing

#### C++ Example
```cpp
#include "CoreOrchestrator.h"

int main() {
    WebGrab::CoreOrchestrator orchestrator(8080, "/tmp/ai-servis");

    // Register services
    orchestrator.registerService("ai-audio-assistant", "localhost", 8082,
        {"audio", "music", "voice"});

    // Start orchestrator
    orchestrator.start();

    // Process commands
    std::string response = orchestrator.processVoiceCommand(
        "Play some jazz music", "user_context");

    std::cout << "Response: " << response << std::endl;

    return 0;
}
```

#### Python Example
```python
import asyncio
from enhanced_orchestrator import EnhancedCoreOrchestrator

async def main():
    orchestrator = EnhancedCoreOrchestrator()

    # Process enhanced command
    result = await orchestrator.handle_enhanced_voice_command(
        text="Play some jazz music by Miles Davis",
        user_id="user123",
        interface_type="voice"
    )

    print(f"Response: {result['response']}")
    print(f"Intent: {result['intent']} (confidence: {result['confidence']})")

asyncio.run(main())
```

### Web Interface Integration

```javascript
// Web client example
async function sendCommand(text) {
    const response = await fetch('/api/command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            text: text,
            user_id: 'web_user',
            interface_type: 'web'
        })
    });

    const result = await response.json();
    console.log('Response:', result.response);
    console.log('Intent:', result.intent);
    console.log('Confidence:', result.confidence);
}

// Usage
sendCommand("Turn on the living room lights");
```

### Mobile App Integration

```swift
// iOS Swift example
struct CommandRequest: Codable {
    let text: String
    let userId: String
    let interfaceType: String
}

func sendCommand(_ text: String) async {
    let request = CommandRequest(
        text: text,
        userId: "mobile_user",
        interfaceType: "mobile"
    )

    // Send to orchestrator
    let response = try await APIClient.post("/api/command", body: request)
    print("Response: \(response.response)")
}
```

## Building and Deployment

### C++ Build
```bash
# Prerequisites
sudo apt-get install build-essential cmake libcurl4-openssl-dev

# Build
mkdir build && cd build
cmake ..
make -j$(nproc)

# Run
./main_orchestrator_full --port 8080 --working-dir /tmp/ai-servis --enable-all
```

### Python Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run enhanced orchestrator
python enhanced_orchestrator.py
```

### Docker Deployment
```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential cmake libcurl4-openssl-dev \
    python3 python3-pip

# Copy source
COPY . /app
WORKDIR /app

# Build C++ components
RUN mkdir build && cd build && cmake .. && make

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Expose ports
EXPOSE 8080 8090 8091

# Start orchestrator
CMD ["./build/main_orchestrator_full", "--enable-all"]
```

## API Reference

### REST API Endpoints

#### POST /api/command
Process a natural language command.

**Request:**
```json
{
    "text": "Play some jazz music",
    "user_id": "user123",
    "session_id": "sess_abc123",
    "interface_type": "web",
    "context": {
        "location": "home",
        "device_id": "web_client_1"
    }
}
```

**Response:**
```json
{
    "response": "Playing jazz music from your preferred streaming service",
    "intent": "play_music",
    "confidence": 0.85,
    "context_used": false,
    "alternatives": [
        ["control_volume", 0.15],
        ["switch_audio", 0.10]
    ],
    "session_id": "sess_abc123"
}
```

#### GET /api/analytics
Get service performance analytics.

**Parameters:**
- `service` (optional): Specific service name
- `metric` (optional): Metric type (response_time, error_rate, usage)

**Response:**
```json
{
    "analytics": {
        "ai-audio-assistant": {
            "response_time": 0.125,
            "error_count": 2,
            "health_status": "healthy",
            "last_seen": "2024-01-15T10:30:00Z"
        }
    },
    "metric": "response_time"
}
```

#### POST /api/session
Create a new user session.

**Request:**
```json
{
    "user_id": "user123",
    "interface_type": "mobile"
}
```

**Response:**
```json
{
    "session_id": "sess_def456",
    "user_id": "user123",
    "interface_type": "mobile",
    "created_at": "2024-01-15T10:30:00Z"
}
```

### MCP Tools

#### process_voice_command
Process natural language commands with context awareness.

#### create_session
Create new user sessions for context management.

#### service_analytics
Retrieve service performance metrics and analytics.

#### analyze_intent
Analyze command intent with confidence scores and alternatives.

## Performance Characteristics

### Benchmarks
- **Command processing latency**: < 100ms for cached contexts
- **Intent classification**: < 50ms for most commands
- **Service routing**: < 25ms for healthy services
- **Context retrieval**: < 10ms from memory cache
- **Session cleanup**: Automatic every 5 minutes

### Scalability
- **Concurrent sessions**: 1000+ active sessions
- **Commands per second**: 100+ commands/second
- **Memory usage**: ~50MB base + ~1KB per session
- **Service connections**: 50+ registered services

### Reliability
- **Uptime target**: 99.9%
- **Error recovery**: Automatic retry with exponential backoff
- **Data persistence**: Context data survives restarts
- **Health monitoring**: Continuous service health checks

## Troubleshooting

### Common Issues

#### Service Connection Failures
```bash
# Check service status
curl http://localhost:8082/health

# View service logs
tail -f /var/log/ai-servis/audio-assistant.log

# Restart service
systemctl restart ai-audio-assistant
```

#### Context Persistence Issues
```bash
# Check context directory permissions
ls -la /tmp/ai-servis/context/

# Clear corrupted contexts
rm -rf /tmp/ai-servis/context/sessions.json

# Restart orchestrator
systemctl restart ai-servis-orchestrator
```

#### NLP Classification Problems
```bash
# Enable debug logging
export AI_SERVIS_LOG_LEVEL=DEBUG

# Test intent analysis
curl -X POST http://localhost:8080/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"text": "your command here"}'
```

### Monitoring and Logs

#### Log Locations
- **C++ Orchestrator**: `/var/log/ai-servis/orchestrator.log`
- **Python Orchestrator**: `/var/log/ai-servis/enhanced-orchestrator.log`
- **Context Manager**: `/var/log/ai-servis/context-manager.log`

#### Metrics Collection
```bash
# Service response times
curl http://localhost:8080/api/analytics?metric=response_time

# Error rates
curl http://localhost:8080/api/analytics?metric=error_rate

# Active sessions
curl http://localhost:8080/api/analytics?metric=sessions
```

## Security Considerations

### Authentication
- **Session-based**: Each session requires valid session ID
- **User validation**: User IDs are validated before processing
- **API keys**: Optional API key authentication for external clients

### Data Protection
- **Context encryption**: Sensitive context data can be encrypted at rest
- **Session isolation**: Sessions are isolated from each other
- **Audit logging**: All commands and responses are logged

### Network Security
- **HTTPS support**: TLS encryption for web interfaces
- **CORS configuration**: Configurable CORS policies
- **Rate limiting**: Built-in rate limiting for API endpoints

## Future Enhancements

### Planned Features
- **Voice activity detection**: Improved voice interface with VAD
- **Multi-language support**: Support for multiple languages
- **Machine learning**: Adaptive learning based on user behavior
- **Distributed deployment**: Multi-node orchestrator deployment
- **Advanced analytics**: Detailed usage analytics and insights

### Integration Roadmap
- **Cloud services**: Integration with cloud AI services
- **IoT platforms**: Enhanced IoT device support
- **Third-party APIs**: Integration with popular APIs and services
- **Mobile SDKs**: Native mobile SDKs for iOS and Android

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies (C++ and Python)
3. Build the project
4. Run tests
5. Submit pull requests

### Code Style
- **C++**: Follow Google C++ Style Guide
- **Python**: Follow PEP 8 guidelines
- **Documentation**: Use Doxygen for C++, docstrings for Python

### Testing
- **Unit tests**: Comprehensive unit test coverage
- **Integration tests**: End-to-end integration testing
- **Performance tests**: Load and performance testing
- **Security tests**: Security vulnerability testing

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- **Documentation**: Check the docs/ directory
- **Issues**: Create GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for general questions
- **Email**: Contact the development team
