FROM nikolaik/python-nodejs:python3.11-nodejs20

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        curl \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN python -m pip install --upgrade pip setuptools wheel

# Modern MongoDB async driver
RUN python -m pip install --no-cache-dir \
    "motor>=3.6.0" \
    "pymongo>=4.9.0"

RUN python -m pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/start

CMD ["bash", "/app/start"]
