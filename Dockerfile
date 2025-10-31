# app/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system packages needed for psycopg2-binary and SSL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 443
CMD ["python", "app.py"]