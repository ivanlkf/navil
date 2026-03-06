# ── Stage 1: Build the Vite/React dashboard ──────────────────────────────────
FROM node:20-alpine AS dashboard-builder
WORKDIR /app/dashboard

COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci --ignore-scripts

COPY dashboard/ ./

# Clerk publishable key is baked into the JS bundle at build time.
# Set this as a Build Variable in Railway (not a runtime variable).
ARG VITE_CLERK_PUBLISHABLE_KEY
ENV VITE_CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLISHABLE_KEY

RUN npm run build

# ── Stage 2: Python backend ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build-time deps for native extensions (cryptography, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy project metadata + source
COPY pyproject.toml README.md LICENSE ./
COPY navil/ ./navil/

# Install navil with cloud + llm extras.
# ml (scikit-learn) is omitted to keep the image lean; add navil[ml] if needed.
RUN pip install -e ".[cloud,llm]"

# Copy the built dashboard into the expected location
COPY --from=dashboard-builder /app/dashboard/dist ./dashboard/dist

EXPOSE 8484

# Railway injects $PORT at runtime; fall back to 8484 locally.
CMD ["sh", "-c", "python -m navil cloud serve --host 0.0.0.0 --port ${PORT:-8484}"]
