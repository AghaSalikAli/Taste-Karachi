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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --ignore-installed

# Copy application code
COPY . .

# Expose ports (8000 for FastAPI, 8501 for Streamlit)
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
