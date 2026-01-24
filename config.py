# config.py
import os
import random

CSV_FILE = r"C:\Users\nikki\AppData\Local\Temp\boss_urls.csv"
HEADERS_FILE = r"C:\Users\nikki\AppData\Local\Temp\headers.csv"
TIMEOUT = 30  # Reduced from 60
OUTPUT_FOLDER = r"C:\Users\nikki\AppData\Local\Temp\RuneScapeData"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# OPTIMIZED ROBOTS.TXT COMPLIANT SETTINGS
WORKERS = 2            # Increased to 2 (safe compromise)
MIN_DELAY = 0.3        # Reduced
MAX_DELAY = 0.8        # Reduced
RETRY_ATTEMPTS = 1
BOSS_DELAY = 0.2       # Reduced between batches
MAX_PAGES = 18

# NEW OPTIMIZATION SETTINGS
ENABLE_SESSION_REUSE = True  # Reuse HTTP sessions
SESSION_TIMEOUT = 300        # Recreate session every 5 minutes
USE_CONNECTION_POOL = True

print(f"⚙️ Optimized config loaded:")
print(f"  - WORKERS: {WORKERS}")
print(f"  - Delays: {MIN_DELAY}-{MAX_DELAY}s")