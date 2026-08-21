"""
On a resource-constrained host (e.g. Railway's $5/mo tier), downloaded
songs pile up in downloads/ over time and can fill up limited disk space.
This periodically clears out files older than a couple hours (safely past
any normal song length) so disk usage stays low.
"""
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler

DOWNLOADS_DIR = "downloads"
MAX_AGE_SECONDS = 2 * 60 * 60  # 2 hours


def cleanup_old_downloads():
    if not os.path.isdir(DOWNLOADS_DIR):
        return
    now = time.time()
    removed = 0
    for fname in os.listdir(DOWNLOADS_DIR):
        fpath = os.path.join(DOWNLOADS_DIR, fname)
        try:
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > MAX_AGE_SECONDS:
                os.remove(fpath)
                removed += 1
        except Exception:
            pass
    if removed:
        print(f"[Cleanup] Removed {removed} old file(s) from {DOWNLOADS_DIR}/")


scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(cleanup_old_downloads, trigger="interval", hours=1)
scheduler.start()
