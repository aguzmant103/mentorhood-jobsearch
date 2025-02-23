# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN python -m pip install --upgrade pip wheel setuptools

# Copy requirements and install Python dependencies
COPY requirements.txt .
# Install packages one by one to better identify any issues
RUN pip install --no-cache-dir python-dotenv>=0.19.0 && \
    pip install --no-cache-dir PyPDF2>=3.0.1 && \
    pip install --no-cache-dir langchain-openai==0.3.1 && \
    pip install --no-cache-dir playwright>=1.41.0 && \
    pip install --no-cache-dir pydantic>=2.0.0 && \
    pip install --no-cache-dir fastapi>=0.68.0 && \
    pip install --no-cache-dir "uvicorn[standard]>=0.15.0" && \
    pip install --no-cache-dir requests>=2.31.0 && \
    pip install --no-cache-dir browser-use==0.1.39

# Install playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Set environment variables
ENV CHROME_PATH=/usr/bin/chromium
ENV BROWSER_USE_CHROME_PATH=/usr/bin/chromium
ENV BROWSER_USE_ARGS="--no-sandbox --disable-dev-shm-usage --headless --disable-gpu --remote-debugging-port=9222"
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PORT=${PORT:-8000}
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Command to run the application
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 75 