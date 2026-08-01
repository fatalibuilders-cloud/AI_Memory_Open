# Small image: the bot's only runtime dependency is a WebSocket client.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY deriv_bot ./deriv_bot

# Run as a non-root user; give it ownership of the state directory so the
# daily counters and trade journal survive restarts on a mounted volume.
RUN useradd --create-home --uid 10001 bot \
    && mkdir -p /app/state \
    && chown -R bot:bot /app
USER bot

VOLUME ["/app/state"]

CMD ["python", "-m", "deriv_bot"]
