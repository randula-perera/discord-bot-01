FROM python:3.10-slim

# FFmpeg සහ අවශ්‍ය දේවල් ඉන්ස්ටෝල් කිරීම
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements ඉන්ස්ටෝල් කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# සියලුම ෆයිල් කොපි කිරීම
COPY . .

# බොට්ව පණ ගැන්වීම
CMD ["python", "main.py"]
