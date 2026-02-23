FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .
COPY examples.py .
COPY quickstart.py .
COPY telegram_bot.py .
COPY platform_integrations.py .
COPY config_example.py .

# Create volume for data persistence
VOLUME ["/app/data"]

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV BOT_STORAGE_FILE=/app/data/posts.json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from bot import AutoPostBot; bot = AutoPostBot(); print('OK')" || exit 1

# Default command
CMD ["python", "bot.py"]
