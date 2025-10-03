# AI-SERVIS Universal

A comprehensive, cross-platform AI assistant ecosystem built with modular MCP (Model Context Protocol) architecture. Transform your environment into an intelligent, voice-controlled system that can manage audio, communications, social media, and platform operations.

## 🌟 Features

### 🎵 **Audio Assistant**
- **Cross-Platform Audio**: Linux (PipeWire/ALSA), Windows (WASAPI), macOS (Core Audio)
- **Voice Processing**: Wake word detection, speech recognition, text-to-speech
- **Music Integration**: Spotify, Apple Music, local files with playlist management
- **Multi-Room Audio**: Zone-based audio control with synchronization
- **Advanced Features**: Audio format conversion, routing, and effects

### 📱 **Communications Hub**
- **SMS/MMS**: Twilio integration with delivery tracking
- **Email**: SMTP/IMAP support with attachment handling
- **Social Media**: WhatsApp, Telegram, Twitter/X, Signal, Facebook Messenger
- **Message Queue**: Reliable delivery with retry logic and priority handling
- **Contact Management**: Unified contact system across all platforms

### 🖥️ **Platform Control**
- **System Integration**: Control Linux, Windows, macOS systems
- **File Operations**: File management and system commands
- **Process Management**: Application control and monitoring
- **Mobile Bridge**: Android and iOS integration capabilities

### 🤖 **AI Orchestration**
- **Natural Language Processing**: Intent recognition and context management
- **Command Processing**: Intelligent command routing and execution
- **Service Discovery**: Automatic service registration and discovery
- **Multi-Modal Interface**: Voice, text, web, and mobile interfaces

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+ (for development)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sparesparrow/ai-servis-universal.git
cd ai-servis-universal
```

2. **Configure the system**
```bash
cp config.json.example config.json
# Edit config.json with your service credentials
```

3. **Start the system**
```bash
docker-compose -f docker-compose.universal.yml up -d
```

4. **Access the services**
- Core Orchestrator: http://localhost:8000
- Audio Assistant: http://localhost:8001
- Communications: http://localhost:8002
- Platform Controller: http://localhost:8003
- Service Discovery: http://localhost:8004
- Grafana Monitoring: http://localhost:3000

## 📋 Configuration

### Environment Variables
Set these environment variables or configure them in `config.json`:

```bash
# Core Services
export MQTT_BROKER=localhost
export REDIS_HOST=localhost
export POSTGRES_HOST=localhost

# Audio Services
export AUDIO_DEVICE=auto
export WAKE_WORD="hey ai servis"

# Communications
export TWILIO_ACCOUNT_SID=your_twilio_sid
export TWILIO_AUTH_TOKEN=your_twilio_token
export SMTP_HOST=smtp.gmail.com
export SMTP_USERNAME=your_email@gmail.com
export SMTP_PASSWORD=your_app_password

# Social Media
export TELEGRAM_BOT_TOKEN=your_telegram_token
export TWITTER_BEARER_TOKEN=your_twitter_token
export WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
```

### Service Configuration
Each module can be configured independently:

- **Audio Assistant**: Configure audio devices, voice settings, music services
- **Communications**: Set up messaging services and social media accounts
- **Platform Control**: Configure system access and security settings
- **Core Orchestrator**: Set up AI processing and service routing

## 🏗️ Architecture

### Modular Design
The system is built with a modular architecture where each component is an independent MCP server:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Core           │    │  Audio          │    │  Communications │
│  Orchestrator   │◄──►│  Assistant      │◄──►│  Hub            │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Platform       │    │  Service        │    │  Security &     │
│  Controllers    │    │  Discovery      │    │  Authentication │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### MCP Protocol
All services communicate using the Model Context Protocol:
- **JSON-RPC 2.0**: Standardized communication protocol
- **Transport Layers**: STDIO, HTTP, WebSocket, MQTT
- **Service Discovery**: Automatic service registration and discovery
- **Tool Exposure**: Each service exposes its capabilities as MCP tools

## 🎯 Usage Examples

### Voice Commands
```bash
# Audio Control
"Hey AI Servis, play music on Spotify"
"Set volume to 50% in the living room"
"Create a new audio zone called 'bedroom'"

# Communications
"Send a WhatsApp message to John saying hello"
"Check my email for new messages"
"Post a tweet about the weather"

# System Control
"Open Chrome browser"
"Show me running processes"
"Create a new file called 'notes.txt'"
```

### API Usage
```python
# Send a message via the communications hub
import requests

response = requests.post('http://localhost:8002/send_message', json={
    'type': 'sms',
    'to': '+1234567890',
    'body': 'Hello from AI-SERVIS!'
})

# Control audio playback
response = requests.post('http://localhost:8001/play_music', json={
    'service': 'spotify',
    'query': 'jazz music',
    'zone': 'living_room'
})
```

## 🔧 Development

### Module Structure
```
modules/
├── core-orchestrator/          # Main orchestration service
├── ai-audio-assistant/         # Audio processing and control
├── ai-communications/          # Messaging and social media
├── ai-platform-controllers/    # System control interfaces
├── service-discovery/          # Service registration and discovery
└── mcp_framework.py           # Shared MCP framework
```

### Adding New Services
1. Create a new module directory
2. Implement the MCP server interface
3. Define your service's tools and capabilities
4. Register with the service discovery system
5. Update the Docker Compose configuration

### Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run system tests
pytest tests/system/
```

## 📊 Monitoring

### Grafana Dashboards
Access comprehensive monitoring at http://localhost:3000:
- **Service Health**: Real-time service status and performance
- **Audio Metrics**: Audio processing and playback statistics
- **Communication Stats**: Message delivery and social media metrics
- **System Resources**: CPU, memory, and network usage

### Logs
All services log to the `logs/` directory with structured logging:
```bash
# View real-time logs
docker-compose -f docker-compose.universal.yml logs -f

# View specific service logs
docker-compose -f docker-compose.universal.yml logs -f audio-assistant
```

## 🔒 Security

### Authentication
- **JWT Tokens**: Secure authentication with configurable expiration
- **API Keys**: Encrypted storage and management of service credentials
- **RBAC**: Role-based access control for different user types

### Privacy
- **Local Processing**: All AI processing happens locally by default
- **Encrypted Storage**: Sensitive data encrypted at rest
- **Audit Logging**: Comprehensive audit trail for all operations

## 🌐 Platform Support

### Desktop Platforms
- **Linux**: Full support with PipeWire/ALSA audio
- **Windows**: Complete integration with WASAPI audio
- **macOS**: Native support with Core Audio

### Mobile Platforms
- **Android**: ADB-based control and integration
- **iOS**: Shortcuts integration and limited system control

### Embedded Platforms
- **Raspberry Pi**: GPIO simulation and hardware control
- **RTOS**: Framework for embedded device integration

## 📚 Documentation

- [Architecture Guide](docs/architecture/)
- [API Reference](docs/api/)
- [Module Documentation](docs/modules/)
- [Deployment Guide](docs/deployment/)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Check the comprehensive documentation
- **Examples**: See the examples directory for usage patterns

## 🎉 Acknowledgments

- Built with the Model Context Protocol (MCP) framework
- Integrates with major audio, messaging, and social media platforms
- Designed for privacy-first, edge-computing environments
- Community-driven development and support

---

**Transform your environment into an intelligent, voice-controlled ecosystem with AI-SERVIS Universal!**
