FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/

RUN mkdir -p /workspace /app/logs

EXPOSE 8000

ENV PYTHONPATH=/app/src

CMD ["python", "src/server.py"]
