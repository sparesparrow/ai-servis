# AI Audio Assistant - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    pulseaudio-utils \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create audio directories
RUN mkdir -p audio/cache audio/temp audio/playlists

# Create non-root user
RUN useradd -m -u 1000 audioassistant && \
    chown -R audioassistant:audioassistant /app

# Switch to non-root user
USER audioassistant

# Expose port
EXPOSE 8086

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8086/health')" || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV AUDIO_DEFAULT_VOLUME=0.5
ENV AUDIO_MAX_VOLUME=1.0
ENV AUDIO_BUFFER_SIZE=4096
ENV AUDIO_SAMPLE_RATE=44100
ENV AUDIO_CHANNELS=2
ENV AUDIO_BIT_DEPTH=16
ENV AUDIO_AUTO_PLAY=true
ENV AUDIO_GAPLESS_PLAYBACK=true

# Start the audio assistant service
CMD ["python", "main.py"]