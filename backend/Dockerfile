# syntax=docker/dockerfile:1.6
#
# Build context = repository root (so both backend/ and frontend/ are visible).
#   docker build -f backend/Dockerfile -t spectralbridge .

# ---------- Stage 1: build the frontend ----------
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: python runtime (serves API + SPA) ----------
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/
COPY backend/scripts/ ./scripts/

# pre-built ML artifacts + dataset -> instant startup, zero network needed
COPY backend/artifacts/ ./artifacts/
COPY backend/data/ ./data/

# built frontend lands at /frontend/dist (matches app.config._FRONTEND_DIST)
COPY --from=frontend /fe/dist /frontend/dist

EXPOSE 8000
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
