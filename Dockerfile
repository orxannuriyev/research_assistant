# Build dependencies in a separate stage so the runtime image does not retain
# pip's build cache or the installer environment.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN python -m venv /opt/venv \
	&& /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY ai ./ai
COPY data ./data
COPY src ./src
COPY api.py app.py demo_ai.py researcher.py .

RUN useradd --create-home --shell /bin/bash appuser \
	&& mkdir -p /app/.cache \
	&& chown -R appuser:appuser /app
USER appuser

CMD ["python", "demo_ai.py", "--offline", "--limit", "5"]
