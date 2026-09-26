FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.12-slim
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels && useradd --uid 10001 --create-home app
COPY --chown=10001:10001 app.py .
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2)"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "20", "--no-access-log"]
