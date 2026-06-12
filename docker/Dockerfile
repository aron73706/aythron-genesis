# Use official lightweight Python image
FROM python:3.12-slim

# Set environment variable to ensure logs are printed immediately
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set workspace directory
WORKDIR /app

# Install system dependencies if needed (none are strictly required for our deps, but good practice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose server port
EXPOSE 8000

# Start server
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
