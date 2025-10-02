# PENIN-Ω Multi-Platform Production Dockerfile
# Supports: linux/amd64, linux/arm64
# Build: docker buildx build --platform linux/amd64,linux/arm64 -t penin-omega .

# ========================================
# Stage 1: Builder
# ========================================
FROM python:3.11-slim as builder

# Build arguments
ARG VERSION=dev
ARG BUILD_DATE
ARG TARGETPLATFORM
ARG TARGETARCH

LABEL org.opencontainers.image.title="PENIN-Ω Builder"
LABEL org.opencontainers.image.description="IA³ Auto-Evolution System Builder"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/danielgonzagat/peninaocubo"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libc-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt pyproject.toml README.md ./
COPY penin/ ./penin/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# ========================================
# Stage 2: Runtime
# ========================================
FROM python:3.11-slim

# Build arguments
ARG VERSION=dev
ARG BUILD_DATE
ARG TARGETPLATFORM
ARG TARGETARCH

# Metadata
LABEL org.opencontainers.image.title="PENIN-Ω"
LABEL org.opencontainers.image.description="IA³ Auto-Evolution System"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/danielgonzagat/peninaocubo"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.authors="Daniel Penin"
LABEL platform="${TARGETPLATFORM}"
LABEL arch="${TARGETARCH}"

# Create non-root user
RUN groupadd -r penin && useradd -r -g penin -u 1000 penin

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY --chown=penin:penin penin/ ./penin/
COPY --chown=penin:penin policies/ ./policies/
COPY --chown=penin:penin deploy/entrypoint.sh /entrypoint.sh

# Create necessary directories
RUN mkdir -p /data /var/log/penin && \
    chown -R penin:penin /data /var/log/penin && \
    chmod +x /entrypoint.sh

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PENIN_DATA_DIR=/data \
    PENIN_LOG_DIR=/var/log/penin \
    PENIN_METRICS_BIND_HOST=0.0.0.0 \
    PENIN_METRICS_PORT=8000

# Expose ports
EXPOSE 8000 8010 8011 8012 8013

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER penin

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["penin", "run", "--host", "0.0.0.0", "--port", "8000"]
