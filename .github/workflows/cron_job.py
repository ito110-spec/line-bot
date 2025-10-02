# cron_runner.py
import requests
import os
import time

TARGET_URL = "https://line-bot-1-rsyx.onrender.com/cron"

print("[CRON] Starting Render Cron Job...")
try:
    print(f"[CRON] Pinging {TARGET_URL}")
    resp = requests.get(TARGET_URL, timeout=30)
    print(f"[CRON] Status code: {resp.status_code}")
    print(f"[CRON] Response: {resp.text}")

except Exception as e:
    print(f"[CRON] Error: {e}")
