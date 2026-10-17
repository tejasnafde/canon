FROM python:3.12-slim
RUN pip install --no-cache-dir uv  # ponytail: pip, not ghcr COPY (ghcr rate-limits Cloud Build)
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project
COPY canon ./canon
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
CMD exec uvicorn canon.app:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'
