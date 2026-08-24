FROM python:3.11-slim

WORKDIR /app

# Dependency system minimal (sqlite3 sudah include di base image python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Folder untuk simpan SQLite db biar bisa di-mount sebagai volume
RUN mkdir -p /app/data

CMD ["python", "bot.py"]