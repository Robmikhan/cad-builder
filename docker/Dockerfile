# ── Stage 1: Build frontend ──
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python + CUDA runtime ──
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip \
    git curl wget unzip \
    ffmpeg libgl1-mesa-glx libglib2.0-0 \
  && ln -sf /usr/bin/python3.11 /usr/bin/python \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -U pip wheel && \
    pip install --no-cache-dir -e ".[gpu]" 2>/dev/null || pip install --no-cache-dir -e .

COPY . /app

# Copy built frontend
COPY --from=frontend-build /frontend/dist /app/frontend/dist

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

CMD ["python", "-m", "uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
