FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/appuser/.cache/huggingface \
    PYTHONPATH=.

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser && \
    mkdir -p /home/appuser/.cache /home/appuser/app/models/tokenizer /home/appuser/app/models/embeddings && \
    chown -R appuser:appuser /home/appuser

WORKDIR /home/appuser/app
    
COPY --chown=appuser:appuser ./docker/embeddings-api/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

USER appuser

ARG TOKENIZER_MODEL
ARG EMBEDDINGS_MODEL

ENV TOKENIZER_MODEL=${TOKENIZER_MODEL} \
    EMBEDDINGS_MODEL=${EMBEDDINGS_MODEL}

COPY --chown=appuser:appuser ./embeddings-api/scripts/download_models.py ./scripts/download_models.py
RUN python3 scripts/download_models.py

COPY --chown=appuser:appuser ./embeddings-api/ .