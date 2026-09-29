FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and setup files
COPY pyproject.toml README.md ./

# Install python packages
RUN pip install --no-cache-dir -e .

# Copy application source code
COPY . .

# Ensure data directories exist
RUN mkdir -p data/db data/cache/pages data/cache/curriculum data/exports data/logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
