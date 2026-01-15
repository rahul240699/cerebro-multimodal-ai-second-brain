FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend directory
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from backend directory
COPY backend/ .

# Create uploads directory
RUN mkdir -p uploads

# Railway uses $PORT environment variable
EXPOSE 8000

# Run application (Railway will inject $PORT)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
