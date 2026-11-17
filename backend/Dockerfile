FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.lock ./
RUN pip install -r requirements.lock \
    && groupadd --gid 10001 smartmim \
    && useradd --uid 10001 --gid smartmim --no-create-home smartmim \
    && mkdir /data && chown smartmim:smartmim /data
COPY --chown=smartmim:smartmim app ./app
USER smartmim
ENV DATABASE_URL=sqlite:////data/smartmim.db
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
