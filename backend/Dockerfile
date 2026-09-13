FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 maje && \
    mkdir -p /maje/scripts /maje/tools /maje/skills /maje/files \
             /maje/soul/memory /maje/workspace /maje/keys && \
    chown -R maje:maje /maje

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy config (api_keys.py is bind-mounted at runtime, not baked in)
RUN chown -R maje:maje /app

USER maje

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
