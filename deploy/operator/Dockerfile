FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/danielgonzagat/peninaocubo"
LABEL org.opencontainers.image.description="PENIN-Ω Kubernetes Operator"
LABEL org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy operator code
COPY deploy/operator/penin_operator.py /app/
COPY deploy/operator/requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 operator && \
    chown -R operator:operator /app

USER operator

# Health check endpoint (kopf provides /healthz)
EXPOSE 8080

CMD ["python", "/app/penin_operator.py"]
