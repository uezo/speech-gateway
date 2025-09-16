# Multi-stage build for optimized image
FROM python:3.11-slim AS builder

# Install build dependencies (git needed for GitHub installation)
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy application
COPY --chown=app:app run.py /app/

# Switch to non-root user
USER app

EXPOSE 8000

CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]
