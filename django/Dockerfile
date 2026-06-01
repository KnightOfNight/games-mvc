# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY src/ .

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "game_mvc.asgi:application"]
