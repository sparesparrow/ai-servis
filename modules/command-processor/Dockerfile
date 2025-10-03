# AI-SERVIS Command Processing Pipeline - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create models and data directories
RUN mkdir -p models data/training

# Create non-root user
RUN useradd -m -u 1000 commandprocessor && \
    chown -R commandprocessor:commandprocessor /app

# Switch to non-root user
USER commandprocessor

# Expose port
EXPOSE 8085

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8085/health')" || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV MAX_CONCURRENT_COMMANDS=10
ENV COMMAND_TIMEOUT=30
ENV ENABLE_CACHING=true
ENV CACHE_TTL=3600

# Start the command processing service
CMD ["python", "main.py"]
