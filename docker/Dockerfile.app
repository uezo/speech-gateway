FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 app

# Set working dir
WORKDIR /app

# Copy application
COPY --chown=app:app ./app/ /app/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Switch to non-root user
USER app

EXPOSE 8000
