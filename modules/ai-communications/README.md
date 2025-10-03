# AI Communications Module

A comprehensive messaging system that provides unified access to multiple communication channels including SMS, email, and other messaging services.

## Features

- **Multi-Channel Messaging**: Support for SMS, email, and extensible to other services
- **Message Queue Management**: Reliable message delivery with retry logic and error handling
- **Service Abstraction**: Unified interface for different messaging providers
- **Contact Management**: Centralized contact management across services
- **Delivery Tracking**: Real-time message status and delivery confirmation
- **Priority Handling**: Message prioritization and queue management
- **Retry Strategies**: Configurable retry mechanisms for failed deliveries

## Supported Services

### SMS/MMS
- **Twilio**: Full SMS/MMS support with delivery status tracking
- **Extensible**: Easy to add other SMS providers

### Email
- **SMTP**: Send emails via any SMTP server
- **IMAP**: Receive emails from any IMAP server
- **Attachments**: Support for file attachments
- **HTML/Plain Text**: Support for both HTML and plain text emails

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure services:
```bash
cp config.json.example config.json
# Edit config.json with your service credentials
```

3. Set environment variables (optional):
```bash
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_FROM_NUMBER="+1234567890"
export SMTP_HOST="smtp.gmail.com"
export SMTP_USERNAME="your_email@gmail.com"
export SMTP_PASSWORD="your_app_password"
```

## Configuration

### Twilio SMS Configuration
```json
{
  "twilio": {
    "account_sid": "your_twilio_account_sid",
    "auth_token": "your_twilio_auth_token",
    "from_number": "+1234567890",
    "status_callback": "https://your-domain.com/webhook/twilio/status"
  }
}
```

### Email Configuration
```json
{
  "email": {
    "smtp": {
      "host": "smtp.gmail.com",
      "port": 587,
      "username": "your_email@gmail.com",
      "password": "your_app_password",
      "use_tls": true
    },
    "imap": {
      "host": "imap.gmail.com",
      "port": 993,
      "username": "your_email@gmail.com",
      "password": "your_app_password",
      "use_ssl": true
    }
  }
}
```

## Usage

### Starting the Server
```bash
python main.py
```

### MCP Tools Available

#### Message Sending
- `send_sms`: Send SMS messages via Twilio
- `send_email`: Send email messages via SMTP
- `send_message`: Send messages via any available service

#### Message Receiving
- `receive_messages`: Receive messages from all services
- `get_message_status`: Get delivery status of sent messages

#### Contact Management
- `get_contacts`: Get contacts from messaging services

#### Queue Management
- `get_queue_status`: Get current queue status
- `get_queue_statistics`: Get queue performance statistics
- `clear_queue`: Clear messages from queue

#### Service Management
- `authenticate_services`: Authenticate with all services
- `get_service_status`: Get status of all services

### Example Usage

#### Send SMS
```json
{
  "tool": "send_sms",
  "params": {
    "to": "+1234567890",
    "body": "Hello from AI Communications!",
    "priority": "normal"
  }
}
```

#### Send Email
```json
{
  "tool": "send_email",
  "params": {
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email from AI Communications.",
    "attachments": ["/path/to/file.pdf"],
    "priority": "high"
  }
}
```

#### Receive Messages
```json
{
  "tool": "receive_messages",
  "params": {
    "type": "all",
    "limit": 10
  }
}
```

## Message Queue System

The module includes a sophisticated message queue system with the following features:

### Retry Strategies
- **Immediate**: Retry immediately
- **Exponential Backoff**: Increasing delays between retries
- **Linear Backoff**: Fixed delay between retries
- **Fixed Interval**: Constant delay between retries

### Priority Levels
- **Low**: Lowest priority
- **Normal**: Standard priority
- **High**: High priority
- **Urgent**: Highest priority

### Queue Statistics
- Total messages processed
- Success/failure rates
- Average delivery time
- Retry attempts
- Queue sizes per service

## Error Handling

The system includes comprehensive error handling:

- **Service Failures**: Automatic retry with configurable strategies
- **Network Issues**: Graceful handling of network timeouts
- **Authentication Errors**: Clear error messages for auth failures
- **Rate Limiting**: Respect for service rate limits
- **Message Validation**: Input validation for all message types

## Extensibility

The module is designed to be easily extensible:

### Adding New Services
1. Create a new service class inheriting from `MessagingService`
2. Implement required abstract methods
3. Add service initialization to `MessagingServiceManager`
4. Update configuration schema

### Adding New Message Types
1. Add new type to `MessageType` enum
2. Update message parsing logic
3. Add service-specific handling

## Monitoring and Logging

- **Structured Logging**: JSON-formatted logs for easy parsing
- **Performance Metrics**: Delivery times, success rates, queue statistics
- **Error Tracking**: Detailed error logging with context
- **Health Checks**: Service availability monitoring

## Security Considerations

- **Credential Management**: Secure storage of API keys and passwords
- **Message Encryption**: Support for encrypted message transmission
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Sanitization of all inputs
- **Audit Logging**: Comprehensive audit trail

## Testing

Run tests with:
```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This module is part of the AI-SERVIS Universal project and follows the same licensing terms.