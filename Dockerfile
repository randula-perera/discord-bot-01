FROM python:3.10-slim

# Install system dependencies for FFmpeg and Voice
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements install කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ඉතිරි files copy කිරීම
COPY . .

# Bot එක run කරන විධානය
CMD ["python", "bot.py"]
