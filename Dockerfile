FROM node:18-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY backend/ /app/

COPY --from=frontend-builder /frontend/dist /app/frontend/dist

RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "core.wsgi"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "core.wsgi:application"]