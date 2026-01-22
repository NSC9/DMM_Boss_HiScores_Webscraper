# scraper.py
import requests
import time
from bs4 import BeautifulSoup
from config import TIMEOUT, RETRY_ATTEMPTS, MIN_DELAY, MAX_DELAY
import random

# Try to import header_rotator, but handle if it fails
try:
    from header_rotator import global_header_rotator as header_rotator
    # print(f"✅ Header rotator imported successfully")
except Exception as e:
    print(f"❌ Failed to import header rotator: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a simple fallback
    class FallbackHeaderRotator:
        def __init__(self):
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'From': 'research@example.com',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Referer': 'https://www.runescape.com/',
            }
            self.worker_headers = {}
        
        def get_headers_for_worker(self, worker_id):
            if worker_id not in self.worker_headers:
                self.worker_headers[worker_id] = self.headers.copy()
            return self.worker_headers[worker_id]
        
        def rotate_worker_headers(self, worker_id):
            return self.get_headers_for_worker(worker_id)
        
        def get_headers_count(self):
            return 1
    
    header_rotator = FallbackHeaderRotator()
    print(f"🔄 Using fallback header rotator")

def scrape_page(boss_name, url, page, worker_id=0):
    """Scrape one page with rotating headers per worker"""
    #print(f"\n📄 Worker {worker_id} scraping {boss_name} page {page}")
    
    # Build URL
    try:
        if 'page=' in url:
            page_url = url.replace('page=1', f'page={page}')
        else:
            page_url = f"{url}&page={page}" if '?' in url else f"{url}?page={page}"
        
        #print(f"🔗 URL: {page_url}")
    except Exception as e:
        print(f"❌ Error building URL: {e}")
        return []
    
    # Get headers for this worker
    try:
        headers = header_rotator.get_headers_for_worker(worker_id)
        #print(f"🔤 Worker {worker_id} headers loaded")
    except Exception as e:
        print(f"❌ Error getting headers: {e}")
        return []
    
    # Add cache-busting parameter
    cache_buster = int(time.time() * 1000)
    if '?' in page_url:
        page_url = f"{page_url}&_={cache_buster}"
    else:
        page_url = f"{page_url}?_={cache_buster}"
    
    # === FIX STARTS HERE - MAKE SURE THIS IS PROPERLY INDENTED ===
    retry_count = 0
    max_retries = 100
    base_delay = 1
    
    while True:  # <-- THIS LINE SHOULD BE AT THE SAME LEVEL AS retry_count = 0
        try:
            # Random delay
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            #print(f"⏱️ Worker {worker_id} waiting {delay:.1f}s before request...")
            time.sleep(delay)
            
            #print(f"🌐 Worker {worker_id} making request (attempt {retry_count + 1})...")
            response = requests.get(
                page_url, 
                headers=headers, 
                timeout=TIMEOUT,
                verify=True
            )
            
            #print(f"📡 Worker {worker_id} got status code: {response.status_code}")
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"⏸️ Worker {worker_id} rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                headers = header_rotator.rotate_worker_headers(worker_id)
                retry_count += 1
                continue
                
            # Handle IP block
            if response.status_code in [403, 503]:
                print(f"🚫 Worker {worker_id} IP blocked. Waiting 5 minutes...")
                time.sleep(300)
                headers = header_rotator.rotate_worker_headers(worker_id)
                retry_count += 1
                continue
                
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main table
            table = soup.find('table')
            if not table:
                print(f"⚠️ Worker {worker_id}: No table found in HTML")
                time.sleep(60)
                retry_count += 1
                continue
            
            # Extract rows
            rows = []
            for tr in table.find_all('tr')[1:]:  # Skip header row
                cells = tr.find_all('td')
                if len(cells) >= 3:
                    rank = cells[0].get_text(strip=True)
                    name = cells[1].get_text(strip=True)
                    score = cells[2].get_text(strip=True)
                    rows.append([rank, name, score])
            
            if rows:
                #print(f"✅ Worker {worker_id}: Successfully extracted {len(rows)} players")
                return rows
            else:
                print(f"⚠️ Worker {worker_id}: No player data found in table")
                time.sleep(30)
                retry_count += 1
                continue
                
        except requests.exceptions.Timeout:
            print(f"⏱️ Worker {worker_id}: Timeout")
            print(f"⏸️ Waiting {base_delay}s...")
            time.sleep(base_delay)
            retry_count += 1
            base_delay = min(base_delay * 1.5, 300)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Worker {worker_id}: Request error: {type(e).__name__}")
            print(f"⏸️ Waiting {base_delay}s...")
            time.sleep(base_delay)
            retry_count += 1
            base_delay = min(base_delay * 1.5, 300)
            headers = header_rotator.rotate_worker_headers(worker_id)
            
        except Exception as e:
            print(f"❌ Worker {worker_id}: Unexpected error: {type(e).__name__}")
            print(f"⏸️ Waiting {base_delay}s...")
            time.sleep(base_delay)
            retry_count += 1
            base_delay = min(base_delay * 1.5, 300)
            
        # Safety check
        if retry_count >= max_retries:
            print(f"🚨 Worker {worker_id}: Max retries reached")
            return []