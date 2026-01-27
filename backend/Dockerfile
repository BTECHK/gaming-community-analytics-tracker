FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for asyncpg and hdbscan (C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy all files (need package structure for hatchling)
COPY . .

# Install package in development mode
RUN pip install --no-cache-dir -e .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
