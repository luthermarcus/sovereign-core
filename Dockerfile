FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
RUN mkdir -p /app/logs /root/sovereign-ecosystem/logs
RUN pip install --no-cache-dir rich requests

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python3", "bin/terminal_dashboard.py"]
