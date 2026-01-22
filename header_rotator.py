# header_rotator.py
import pandas as pd
import itertools
import os
import traceback

class HeaderRotator:
    def __init__(self, headers_file):
        print(f"🔄 Initializing HeaderRotator with file: {headers_file}")
        print(f"📂 File exists: {os.path.exists(headers_file)}")
        
        self.headers_file = headers_file
        self.headers_list = []
        self.header_cycle = None
        self.worker_headers = {}
        
        try:
            self.headers_list = self.load_headers(headers_file)
            if self.headers_list:
                print(f"✅ Successfully loaded {len(self.headers_list)} headers")
                self.header_cycle = itertools.cycle(self.headers_list)
            else:
                print("⚠️ No headers loaded, creating default")
                self.headers_list = [self.create_default_header()]
                self.header_cycle = itertools.cycle(self.headers_list)
                
        except Exception as e:
            print(f"❌ Critical error in HeaderRotator.__init__: {e}")
            traceback.print_exc()
            # Create a default header as fallback
            self.headers_list = [self.create_default_header()]
            self.header_cycle = itertools.cycle(self.headers_list)
    
    def load_headers(self, headers_file):
        """Load headers from CSV file with actual column names"""
        headers = []
        
        try:
            if not os.path.exists(headers_file):
                print(f"❌ Headers file not found: {headers_file}")
                return headers
                
            df = pd.read_csv(headers_file)
            
            for _, row in df.iterrows():
                try:
                    # ENCODE ALL HEADER VALUES TO ASCII SAFE STRINGS
                    header_dict = {
                        'User-Agent': self.safe_encode(str(row['user_agent'])),
                        'From': self.safe_encode(str(row['from'])),
                        'Accept': self.safe_encode(str(row['accept'])),
                        'Accept-Language': self.safe_encode(str(row['accept_language'])),
                        'Accept-Encoding': self.safe_encode(str(row['accept_encoding'])),
                        'Connection': self.safe_encode(str(row['connection'])),
                        'Referer': self.safe_encode(str(row['referer']))
                    }
                    headers.append(header_dict)
                        
                except Exception as e:
                    print(f"⚠️ Error processing header row: {e}")
                    continue
            
            print(f"✅ Processed {len(headers)} header configurations")
            return headers
            
        except Exception as e:
            print(f"❌ Error loading headers: {e}")
            return headers
    
    def safe_encode(self, text):
        """Convert text to ASCII-safe string by removing/replacing non-ASCII chars"""
        try:
            # First try to encode as ASCII, replacing non-ASCII with ?
            encoded = text.encode('ascii', 'replace').decode('ascii')
            # Replace the replacement char with dash
            encoded = encoded.replace('?', '-')
            return encoded
        except:
            # If that fails, use a very conservative approach
            # Remove all non-ASCII characters
            return ''.join(char for char in text if ord(char) < 128)
    
    def create_default_header(self):
        """Create a default header if CSV loading fails"""
        print("🛠️ Creating default header")
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'From': 'research@example.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.runescape.com/',
        }
    
    def get_headers_for_worker(self, worker_id):
        """Get headers for a specific worker, cycling through the list"""
        if not self.header_cycle:
            print(f"⚠️ No header cycle for worker {worker_id}, creating default")
            return self.create_default_header()
            
        if worker_id not in self.worker_headers:
            self.worker_headers[worker_id] = next(self.header_cycle)
            print(f"👷 Assigned header to Worker {worker_id}")
        return self.worker_headers[worker_id]
    
    def rotate_worker_headers(self, worker_id):
        """Rotate headers for a specific worker"""
        if not self.header_cycle:
            return self.create_default_header()
            
        new_headers = next(self.header_cycle)
        self.worker_headers[worker_id] = new_headers
        print(f"🔄 Rotated headers for Worker {worker_id}")
        return new_headers
    
    def get_next_headers(self):
        """Get next headers in rotation"""
        if not self.header_cycle:
            return self.create_default_header()
        return next(self.header_cycle)
    
    def get_headers_count(self):
        """Return number of available header configurations"""
        return len(self.headers_list) if self.headers_list else 1

# Create a global instance
try:
    from config import HEADERS_FILE
    print(f"🔧 Creating global_header_rotator with HEADERS_FILE: {HEADERS_FILE}")
    global_header_rotator = HeaderRotator(HEADERS_FILE)
    print(f"✅ Global header rotator created successfully")
except Exception as e:
    print(f"❌ Failed to create global_header_rotator: {e}")
    traceback.print_exc()
    # Create with default path as fallback
    default_path = r"C:\Users\nikki\AppData\Local\Temp\headers.csv"
    print(f"🔄 Trying default path: {default_path}")
    global_header_rotator = HeaderRotator(default_path)