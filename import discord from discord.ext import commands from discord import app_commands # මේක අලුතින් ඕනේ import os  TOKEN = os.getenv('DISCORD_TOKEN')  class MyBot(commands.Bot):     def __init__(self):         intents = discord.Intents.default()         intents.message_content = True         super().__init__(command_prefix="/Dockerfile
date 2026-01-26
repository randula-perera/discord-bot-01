FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg libffi-dev libnacl-dev python3-dev build-essential

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
