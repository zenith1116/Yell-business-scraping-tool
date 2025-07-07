FROM python:3.9-slim
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the application
COPY . .
# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
# Expose port
EXPOSE 5000
# Command to run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"