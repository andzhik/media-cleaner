FROM python:3.12-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src /app/src
RUN pip install --no-cache-dir .

CMD ["python", "-u", "-m", "src.worker.main"]
