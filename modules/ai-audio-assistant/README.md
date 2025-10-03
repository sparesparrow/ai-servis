# AI Audio Assistant Module

The AI Audio Assistant module provides comprehensive audio control capabilities for the AI-SERVIS system, including music playback, voice recognition, text-to-speech, and cross-platform audio management.

## Features

### 🎵 **Music Playback**
- **Multi-format Support**: MP3, WAV, FLAC, AAC, OGG, M4A, WMA
- **Playlist Management**: Create, manage, and play playlists
- **Zone-based Audio**: Multi-room audio with independent zone control
- **Playback Controls**: Play, pause, stop, next, previous, seek
- **Shuffle & Repeat**: Shuffle mode and repeat options (none, one, all)
- **Crossfade & Gapless**: Smooth transitions between tracks

### 🔊 **Audio Device Management**
- **Cross-platform Support**: Linux (PipeWire/ALSA), Windows (WASAPI), macOS (Core Audio)
- **Device Enumeration**: Automatic detection of audio devices
- **Volume Control**: Per-device and per-zone volume management
- **Mute/Unmute**: Device-level audio muting
- **Default Device**: Set and manage default audio output

### 🎤 **Voice Processing**
- **Speech Recognition**: Real-time voice command processing
- **Text-to-Speech**: Natural voice synthesis with multiple voices
- **Voice Commands**: Natural language audio control commands
- **Wake Word Detection**: Voice activity detection and processing
- **Command Patterns**: Extensible voice command recognition

### 🏠 **Multi-Zone Audio**
- **Zone Management**: Create and manage audio zones
- **Independent Control**: Separate volume and playback per zone
- **Zone Synchronization**: Synchronized playback across zones
- **Device Assignment**: Assign audio devices to specific zones
- **Session Management**: User-specific audio sessions

## Architecture

### Core Components

1. **Audio Engine**: Cross-platform audio system abstraction
2. **Music Player**: PyGame-based audio playback engine
3. **Voice Processor**: Speech recognition and TTS system
4. **Audio Manager**: Central coordination and management
5. **MCP Server**: Model Context Protocol interface

### Supported Platforms

- **Linux**: PipeWire and ALSA support
- **Windows**: WASAPI integration
- **macOS**: Core Audio support
- **Cross-platform**: PyGame audio backend

## Installation

### Prerequisites

```bash
# Install system audio dependencies
# Linux
sudo apt-get install alsa-utils pulseaudio-utils

# Windows
# No additional dependencies required

# macOS
# No additional dependencies required
```

### Python Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# For audio processing
pip install pyaudio sounddevice librosa

# For music streaming
pip install spotipy youtube-dl

# For voice processing
pip install speechrecognition pyttsx3
```

### Configuration

Set environment variables for configuration:

```bash
# Audio Configuration
export AUDIO_DEFAULT_VOLUME=0.5
export AUDIO_MAX_VOLUME=1.0
export AUDIO_BUFFER_SIZE=4096
export AUDIO_SAMPLE_RATE=44100
export AUDIO_CHANNELS=2
export AUDIO_BIT_DEPTH=16

# Playback Configuration
export AUDIO_CROSSFADE_DURATION=2.0
export AUDIO_FADE_IN_DURATION=1.0
export AUDIO_FADE_OUT_DURATION=1.0
export AUDIO_AUTO_PLAY=true
export AUDIO_GAPLESS_PLAYBACK=true

# Service Integration
export SPOTIFY_CLIENT_ID=your_spotify_client_id
export SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
export YOUTUBE_API_KEY=your_youtube_api_key
```

## Usage

### Basic Audio Control

```python
from ai_audio_assistant import AudioAssistantMCP

# Create audio assistant
audio_assistant = AudioAssistantMCP()
await audio_assistant.start()

# List available devices
devices = await audio_assistant.list_audio_devices()
print(f"Available devices: {devices}")

# Set volume
await audio_assistant.set_volume(0.7)

# Play a track
track = {
    "title": "Example Song",
    "artist": "Example Artist",
    "duration": 180.0,
    "source": "local",
    "format": "mp3",
    "file_path": "/path/to/song.mp3"
}
await audio_assistant.play_track(track, "zone1")
```

### Voice Commands

```python
# Start voice recognition
await audio_assistant.start_voice_recognition()

# Process voice command
command = "play jazz music"
result = await audio_assistant.process_voice_command(command)

# Text-to-speech
await audio_assistant.speak_text("Playing jazz music")
```

### Zone Management

```python
# Create audio zone
zone = await audio_assistant.create_zone("Living Room", ["device1", "device2"])

# Set zone volume
await audio_assistant.set_zone_volume("zone1", 0.8)

# Get zone status
status = await audio_assistant.get_zone_status("zone1")
print(f"Zone status: {status}")
```

## API Reference

### Audio Device Management

#### `list_audio_devices()`
List all available audio devices.

**Returns:** List of audio devices with properties

#### `set_default_device(device_id)`
Set the default audio device.

**Parameters:**
- `device_id` (str): Device identifier

**Returns:** Success status

#### `get_volume(device_id=None)`
Get current volume level.

**Parameters:**
- `device_id` (str, optional): Device ID

**Returns:** Volume level (0.0-1.0)

#### `set_volume(volume, device_id=None)`
Set volume level.

**Parameters:**
- `volume` (float): Volume level (0.0-1.0)
- `device_id` (str, optional): Device ID

**Returns:** Success status

### Music Playback

#### `play_track(track, zone_id)`
Play a track in the specified zone.

**Parameters:**
- `track` (dict): Track information
- `zone_id` (str): Zone identifier

**Returns:** Playback result

#### `pause_playback(zone_id)`
Pause playback in the specified zone.

**Parameters:**
- `zone_id` (str): Zone identifier

**Returns:** Success status

#### `resume_playback(zone_id)`
Resume playback in the specified zone.

**Parameters:**
- `zone_id` (str): Zone identifier

**Returns:** Success status

#### `stop_playback(zone_id)`
Stop playback in the specified zone.

**Parameters:**
- `zone_id` (str): Zone identifier

**Returns:** Success status

### Voice Processing

#### `start_voice_recognition()`
Start voice recognition for commands.

**Returns:** Success status

#### `process_voice_command(command)`
Process a voice command string.

**Parameters:**
- `command` (str): Voice command text

**Returns:** Processed command information

#### `speak_text(text, voice=None)`
Convert text to speech.

**Parameters:**
- `text` (str): Text to speak
- `voice` (str, optional): Voice to use

**Returns:** Success status

## Voice Commands

### Supported Voice Commands

#### Playback Control
- "play music" - Start music playback
- "pause" - Pause current playback
- "resume" - Resume paused playback
- "stop" - Stop playback
- "next song" - Play next track
- "previous song" - Play previous track

#### Volume Control
- "turn up volume" - Increase volume
- "turn down volume" - Decrease volume
- "set volume to 50" - Set specific volume level
- "mute" - Mute audio
- "unmute" - Unmute audio

#### Music Selection
- "play jazz music" - Play jazz genre
- "play song by [artist]" - Play specific artist
- "play [song name]" - Play specific song
- "play album [album name]" - Play specific album

## Troubleshooting

### Common Issues

1. **No Audio Output**
   - Check device connections
   - Verify audio device selection
   - Test with system audio tools

2. **Voice Recognition Not Working**
   - Check microphone permissions
   - Test microphone with system tools
   - Verify speech recognition dependencies

3. **Playback Issues**
   - Check audio file format support
   - Verify file paths and permissions
   - Test with different audio files

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --verbose
```

## License

This module is part of the AI-SERVIS Universal project and follows the same license terms.