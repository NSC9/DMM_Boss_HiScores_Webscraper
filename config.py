# config.py
import os

CSV_FILE = r"C:\Users\nikki\AppData\Local\Temp\boss_urls.csv"
HEADERS_FILE = r"C:\Users\nikki\AppData\Local\Temp\headers.csv"
TIMEOUT = 60
OUTPUT_FOLDER = r"C:\Users\nikki\AppData\Local\Temp\RuneScapeData"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ROBOTS.TXT COMPLIANT SETTINGS
WORKERS = 1          # Number of concurrent workers was4
MIN_DELAY =.5
MAX_DELAY = 1.0
RETRY_ATTEMPTS = 1
BOSS_DELAY = 0.5
MAX_PAGES = 8

# Debug info
print(f"⚙️ Config loaded:")
print(f"  - CSV_FILE: {CSV_FILE}")
print(f"  - HEADERS_FILE: {HEADERS_FILE} (exists: {os.path.exists(HEADERS_FILE)})")
print(f"  - OUTPUT_FOLDER: {OUTPUT_FOLDER}")
print(f"  - WORKERS: {WORKERS}")