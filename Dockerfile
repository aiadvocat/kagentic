FROM python:3.9-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and initialize shared package
RUN mkdir -p /app/shared
COPY shared/db.py /app/shared/
COPY shared/__init__.py /app/shared/

# Add app directory to Python path
ENV PYTHONPATH=/app