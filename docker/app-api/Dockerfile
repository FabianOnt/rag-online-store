FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 appuser &&\
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /home/appuser/app

COPY --chown=appuser:appuser ./app-api/ .
COPY --chown=appuser:appuser ./docker/app-api/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

USER appuser