FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

RUN useradd --create-home appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

USER appuser

ENV DB_PATH=/data/uptime.db

EXPOSE 5050

CMD ["gunicorn", "--bind", "0.0.0.0:5050", "dashboard:app"]