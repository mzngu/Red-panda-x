# server/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add wait-for-it
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Use wait-for-it to delay backend start until Postgres is ready
CMD ["uvicorn", "server.server:app", "--host", "0.0.0.0", "--port", "8080"]

