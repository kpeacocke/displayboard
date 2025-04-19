# === Builder Stage ===
FROM python:alpine AS builder

WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY requirements.txt ./

# Install dependencies (no dev)
RUN pip install --no-cache-dir --requirement requirements.txt \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy the source code
COPY skaven_soundscape ./skaven_soundscape

# Copy entry and metadata files if needed
COPY README.md .


# === Runtime Stage ===
FROM python:alpine

WORKDIR /app

# Copy from builder stage
COPY --from=builder /app /app

# Copy sounds externally via volume in docker-compose

# Default environment variables (override via .env)
ENV SOUND_VOLUME=0.75
ENV USE_GPIO=false
ENV DEBUG_MODE=false

CMD ["poetry", "run", "python", "-m", "skaven_soundscape.main"]
