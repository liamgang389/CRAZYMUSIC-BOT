FROM python:3.13-slim

# --- System dependencies -----------------------------------------------
# ffmpeg   -> required for thumbnails, format conversion, splitting large files
# nodejs   -> required by yt-dlp for YouTube signature/JS-challenge solving.
#             Debian's apt-provided nodejs is too old (v20) for current
#             yt-dlp, which needs Node >= 22 — so we install it from
#             NodeSource's setup script instead of `apt install nodejs npm`.
# gcc/etc  -> needed to build the tgcrypto C extension
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    git \
    curl \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistent-ish local storage for the sqlite fallback DB / logs / temp
# downloads (see README for why you should point DB_DSN at a real MySQL
# instance instead of relying on this for anything you can't lose on redeploy).
RUN mkdir -p /app/logs /app/downloads /app/temp

# main.py is launched as `python src/main.py` (not `cd src && python main.py`):
# Python auto-adds the script's own directory (src/) to sys.path, which is
# what lets `from config import ...` etc. resolve. Keep it this way.
CMD ["python", "src/main.py"]
