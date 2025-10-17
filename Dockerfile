# Use Python 3.11 slim image as base
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libcurl4-openssl-dev \
        libssl-dev \
        libffi-dev \
        libxml2-dev \
        libxslt-dev \
        python3-dev

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir \
--index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
-r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]