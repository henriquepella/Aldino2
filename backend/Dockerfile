FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

# Bibliotecas de sistema para geopandas / pyproj / shapely / matplotlib / psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgeos-dev \
        libproj-dev \
        proj-data \
        proj-bin \
        libspatialindex-dev \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# psycopg2-binary + celery/redis são opcionais no requirements; garantimos aqui
RUN pip install -r requirements.txt psycopg2-binary==2.9.10 celery==5.4.0 redis==5.2.1

COPY . .

RUN mkdir -p /data/storage
ENV STORAGE_DIR=/data/storage

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD curl -fsS http://localhost:8000/api/meta/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
