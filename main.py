# main.py
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import traceback
import sys
import random  # <-- ADD THIS LINE!
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

print("=" * 60)
print("🚀 OSRS HiScores Web Scraper - Starting up")
print("=" * 60)

# Import with error handling
try:
    from config import CSV_FILE, OUTPUT_FOLDER, WORKERS, BOSS_DELAY, MAX_PAGES
    print(f"✅ Config imported")
except Exception as e:
    print(f"❌ Failed to import config: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
    exit()

try:
    from csv_loader import load_boss_urls
    print(f"✅ CSV loader imported")
except Exception as e:
    print(f"❌ Failed to import csv_loader: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
    exit()

try:
    from scraper import scrape_page
    print(f"✅ Scraper imported")
except Exception as e:
    print(f"❌ Failed to import scraper: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
    exit()

try:
    from header_rotator import global_header_rotator as header_rotator
    print(f"✅ Header rotator imported")
except Exception as e:
    print(f"❌ Failed to import header rotator: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
    exit()

print("\n" + "=" * 60)
print("📊 System Diagnostics:")
print(f"  - CSV file exists: {os.path.exists(CSV_FILE)}")
print(f"  - Output folder exists: {os.path.exists(OUTPUT_FOLDER)}")
print(f"  - Available headers: {header_rotator.get_headers_count() if hasattr(header_rotator, 'get_headers_count') else 'N/A'}")
print("=" * 60 + "\n")

class StatusTracker:
    def __init__(self, total_bosses, max_pages_per_boss):
        self.total_bosses = total_bosses
        self.max_pages_per_boss = max_pages_per_boss
        self.completed_bosses = 0
        self.completed_pages = 0
        self.total_pages = total_bosses * max_pages_per_boss
        self.start_time = time.time()
        self.current_bosses = {}
        self.lock = Lock()
        
    def update_boss_status(self, boss_name, current_page, status="processing"):
        with self.lock:
            self.current_bosses[boss_name] = {
                'current_page': current_page,
                'status': status,
                'updated_at': time.time()
            }
            
    def mark_page_complete(self):
        with self.lock:
            self.completed_pages += 1
            
    def mark_boss_complete(self, boss_name):
        with self.lock:
            self.completed_bosses += 1
            if boss_name in self.current_bosses:
                del self.current_bosses[boss_name]
                
    def get_progress(self):
        with self.lock:
            boss_progress = (self.completed_bosses / self.total_bosses) * 100
            page_progress = (self.completed_pages / self.total_pages) * 100
            
            elapsed_time = time.time() - self.start_time
            if self.completed_pages > 0:
                time_per_page = elapsed_time / self.completed_pages
                remaining_pages = self.total_pages - self.completed_pages
                eta_seconds = remaining_pages * time_per_page
                eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                eta_str = eta_time.strftime("%H:%M:%S")
            else:
                eta_str = "Calculating..."
                
            return {
                'boss_progress': boss_progress,
                'page_progress': page_progress,
                'completed_bosses': self.completed_bosses,
                'total_bosses': self.total_bosses,
                'completed_pages': self.completed_pages,
                'total_pages': self.total_pages,
                'eta': eta_str,
                'elapsed': str(timedelta(seconds=int(elapsed_time))),
                'current_bosses': list(self.current_bosses.keys())[:3]  # Show first 3
            }

def clear_status_line():
    """Clear the entire line more thoroughly"""
    sys.stdout.write('\r\033[K')  # \033[K clears from cursor to end of line
    sys.stdout.flush()

def print_status(tracker):
    """Print the status bar and progress information"""
    progress = tracker.get_progress()
    
    # Clear line more thoroughly
    clear_status_line()
    
    # Progress bar
    bar_length = 40
    filled_length = int(bar_length * progress['boss_progress'] / 100)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # Status line
    status_line = f"📊 Progress: [{bar}] {progress['boss_progress']:.1f}% "
    status_line += f"({progress['completed_bosses']}/{progress['total_bosses']} bosses) "
    status_line += f"⏱️ ETA: {progress['eta']} "
    status_line += f"⏳ Elapsed: {progress['elapsed']}"
    
    sys.stdout.write(status_line)
    sys.stdout.flush()

def scrape_boss_worker(boss_name, url, worker_id, tracker, max_pages=MAX_PAGES):
    """Worker function to scrape ALL pages for a boss - KEEP TRYING UNTIL SUCCESS"""
    all_players_data = []
    
    #print(f"\n🎯 Starting {boss_name}...")
    
    for page in range(1, max_pages + 1):
        tracker.update_boss_status(boss_name, page, "scraping")
        
        # KEEP TRYING THIS PAGE UNTIL WE GET DATA
        page_attempts = 0
        while True:
            rows = scrape_page(boss_name, url, page, worker_id)
            
            if rows and len(rows) > 0:
                all_players_data.extend(rows)
                tracker.mark_page_complete()
                tracker.update_boss_status(boss_name, page, f"✓ {len(rows)} players")
                #print(f"   Page {page}: {len(rows)} players")
                break  # Success! Move to next page
            else:
                page_attempts += 1
                print(f"   Page {page}: FAILED attempt {page_attempts}, retrying in 30s...")
                
                # Wait before retrying same page
                time.sleep(random.uniform(0.5, 2))
                
                # Rotate headers for next attempt
                try:
                    header_rotator.rotate_worker_headers(worker_id)
                except:
                    pass
        
        # Small pause between successful pages
        if page < max_pages:
            pause = random.uniform(3, 7)
            #print(f"⏸️  Pausing {pause:.1f}s before page {page + 1}...")
            time.sleep(pause)
    
    tracker.mark_boss_complete(boss_name)
    
    # Report final results
    total_players = len(all_players_data)
    print(f"✅ {boss_name}: COMPLETE - {total_players} players collected")
    
    return boss_name, all_players_data

def process_and_save_boss_data(boss_name, boss_data, tracker):
    """Process and save data for a single boss"""
    if not boss_data:
        return False
    
    try:
        tracker.update_boss_status(boss_name, 0, "saving")
        
        # Convert to DataFrame
        df = pd.DataFrame(boss_data, columns=['Rank', 'Name', 'Score'])
        
        # Clean and format data
        # Convert score (KC) to numeric (remove commas)
        df['Score'] = df['Score'].astype(str).str.replace(',', '').astype(int)
        
        # Calculate total KC (sum of all players' KC)
        total_kc = df['Score'].sum()
        
        # Get total number of players
        total_players = len(df)
        
        # Get current timestamp for Last Updated
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create the final DataFrame in the correct format
        final_df = pd.DataFrame({
            'Boss Name': [boss_name],
            'Total KC': [total_kc],
            'Players': [total_players],
            'Last Updated': [last_updated]
        })
        
        # Save to CSV
        csv_filename = f"{boss_name.replace(' ', '_')}.csv"  # Replace spaces with underscores
        csv_path = os.path.join(OUTPUT_FOLDER, csv_filename)
        final_df.to_csv(csv_path, index=False)
        
        # Clear status line to print success message
        clear_status_line()
        print(f"✅ {boss_name}: {total_players} players, {total_kc:,} total KC")
        
        return True
        
    except Exception as e:
        clear_status_line()
        print(f"❌ Error processing {boss_name}: {e}")
        return False

def main():
    print("🔄 Loading boss URLs...")
    boss_urls = load_boss_urls(CSV_FILE)
    
    if not boss_urls:
        print("❌ No URLs loaded")
        return
    
    print(f"🎯 Found {len(boss_urls)} bosses")
    print(f"👷 Using {WORKERS} workers with {header_rotator.get_headers_count()} rotating headers")
    print(f"📁 Output folder: {OUTPUT_FOLDER}")
    print("\n" + "=" * 60)
    
    # Initialize status tracker
    tracker = StatusTracker(len(boss_urls), MAX_PAGES)
    
    boss_items = list(boss_urls.items())
    successful_bosses = 0
    
    # Process bosses in batches of WORKERS
    for i in range(0, len(boss_items), WORKERS):
        batch = boss_items[i:i + WORKERS]
        
        # Print batch header
        clear_status_line()
        print(f"\n📦 Batch {i//WORKERS + 1}/{(len(boss_items) + WORKERS - 1)//WORKERS}: ", end="")
        print(", ".join([boss[0] for boss in batch]))
        
        try:
            with ThreadPoolExecutor(max_workers=min(len(batch), WORKERS)) as executor:
                futures = []
                
                for worker_id, (boss_name, url) in enumerate(batch):
                    future = executor.submit(
                        scrape_boss_worker, 
                        boss_name, 
                        url, 
                        worker_id % WORKERS,
                        tracker,
                        MAX_PAGES
                    )
                    futures.append(future)
                
                # Process completed bosses
                for future in as_completed(futures):
                    try:
                        boss_name, boss_data = future.result()
                        
                        if process_and_save_boss_data(boss_name, boss_data, tracker):
                            successful_bosses += 1
                            
                        # Update status display
                        print_status(tracker)
                        
                    except Exception as e:
                        clear_status_line()
                        print(f"❌ Error processing future: {e}")
                        traceback.print_exc()
                
        except Exception as e:
            clear_status_line()
            print(f"❌ Error in batch processing: {e}")
            traceback.print_exc()
        
        # Update status after batch completion
        print_status(tracker)
        
        # Delay between batches
        if i + WORKERS < len(boss_items):
            time.sleep(BOSS_DELAY)
            print_status(tracker)
    
    # Final status
    clear_status_line()
    print(f"\n{'='*60}")
    print(f"✅ Scraping complete!")
    print(f"📊 Successfully processed: {successful_bosses}/{len(boss_urls)} bosses")
    
    # Show time statistics
    elapsed = time.time() - tracker.start_time
    avg_time_per_boss = elapsed / successful_bosses if successful_bosses > 0 else 0
    print(f"⏱️ Total time: {str(timedelta(seconds=int(elapsed)))}")
    print(f"📈 Average time per boss: {avg_time_per_boss:.1f} seconds")
    print(f"📁 Check {OUTPUT_FOLDER} for CSV files")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_status_line()
        print("\n\n⚠️ Script interrupted by user")
        
        # Show partial progress if interrupted
        if 'tracker' in locals():
            progress = tracker.get_progress()
            print(f"📊 Partial progress: {progress['completed_bosses']}/{progress['total_bosses']} bosses")
            print(f"⏱️ Time spent: {progress['elapsed']}")
    except Exception as e:
        clear_status_line()
        print(f"\n❌ Unexpected error in main: {e}")
        traceback.print_exc()
    
    input("\nPress Enter to exit...")