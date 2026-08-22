FROM nikolaik/python-nodejs:python3.10-nodejs19

# Ensure Python's stdout/stderr are never buffered — without this, print()
# statements can be delayed or missing from streamed container logs.
ENV PYTHONUNBUFFERED=1

# Debian "buster" reached end-of-life and was moved off the normal mirrors,
# so apt-get update 404s against deb.debian.org. Point it at
# archive.debian.org instead, and temporarily skip the extra nodesource/yarn
# repo files (broken/unsigned) since we only need ffmpeg from Debian itself.
RUN mv /etc/apt/sources.list.d /etc/apt/sources.list.d.bak \
    && sed -i \
       -e 's|deb.debian.org|archive.debian.org|g' \
       -e 's|security.debian.org|archive.debian.org|g' \
       /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mv /etc/apt/sources.list.d.bak /etc/apt/sources.list.d

COPY . /app/
WORKDIR /app/

# Python 3.10 is in use here, so youtubesearchpython must be pinned to a
# version that still supports it (2.3.0+ requires Python 3.11+, and
# 2.5.0+ requires Python 3.12+). Installing this pin BEFORE requirements.txt
# means pip will see it's already satisfied and won't try to upgrade it
# to an incompatible version when processing requirements.txt.
RUN pip3 install --no-cache-dir "youtube-search-python==1.6.6"

RUN pip3 install --no-cache-dir -U -r requirements.txt

CMD ["bash", "start"]
