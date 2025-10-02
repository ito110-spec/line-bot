# cron_job.py
import requests
import time

TARGET_URL = "https://line-bot-1-rsyx.onrender.com/cron"

print("🚀 Starting scheduled cron endpoint call...")
resp = requests.get(TARGET_URL)
print(f"Status: {resp.status_code}, Body: {resp.text}")
