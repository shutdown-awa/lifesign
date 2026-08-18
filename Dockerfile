FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code + config template
COPY app/ ./app/
COPY config/ ./config/

# Single port: /ingest (phone upload) + /query_all (agent) + /mcp (Hermes)
EXPOSE 8764

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8764/health',timeout=3)"

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8764", "--log-level", "info"]
