# rate_limiter.py
import time
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests_per_minute=25):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = Lock()
    
    def wait_if_needed(self):
        with self.lock:
            current_time = time.time()
            # Remove requests older than 1 minute
            self.requests = [t for t in self.requests if current_time - t < 60]
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = 60 - (current_time - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Clear and start fresh
                    self.requests = []
            
            self.requests.append(current_time)

# Create global instance
global_rate_limiter = RateLimiter(max_requests_per_minute=25)