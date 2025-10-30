FROM --platform=$BUILDPLATFORM python:3.10-slim

WORKDIR /app

# Install system dependencies based on platform
RUN apt-get update && \
    case "$(uname -m)" in \
    "x86_64") ARCH="amd64" ;; \
    "aarch64") ARCH="arm64" ;; \
    esac && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --ignore-installed

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
