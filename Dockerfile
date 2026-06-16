# ── ReelIntel Backend ─────────────────────────────────────────────────────────
# Multi-stage build for production deployment
# Requires: GROQ_API_KEY, SERPER_API_KEY as runtime env vars

FROM python:3.11-slim AS base

# System dependencies: ffmpeg for audio extraction, curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp (latest stable)
RUN pip install --no-cache-dir yt-dlp

# ── Build stage ───────────────────────────────────────────────────────────────
FROM base AS builder

WORKDIR /app

# Install Python dependencies first (cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM base AS runtime

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy application code
COPY . .

# Create downloads directory with proper permissions
RUN mkdir -p /app/downloads && chown -R appuser:appuser /app

USER appuser

# Default port (overridable via PORT env var)
ENV PORT=8000
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start with uvicorn — reads HOST/PORT from env
CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --workers ${WORKERS:-1} --log-level ${LOG_LEVEL:-info}"]
