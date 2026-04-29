
FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" 
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
FROM python:3.11-slim AS runtime
RUN groupadd --gid 1000 appgroup \
 && useradd  --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY --chown=appuser:appgroup . .
RUN mkdir -p /app/rag_working/neo4j_import \
 && chown -R appuser:appgroup /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info", "--access-log"]
