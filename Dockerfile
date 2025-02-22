# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Set environment variables
ENV CHROME_PATH=/usr/bin/chromium
ENV PORT=${PORT:-8000}

# Make start script executable
COPY backend/start.sh .
RUN chmod +x start.sh

# Command to run the application
CMD ["./start.sh"] 