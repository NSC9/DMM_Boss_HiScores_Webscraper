# parallel_manager.py
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

class ParallelManager:
    def __init__(self, max_workers, rate_limit_per_minute=25):
        self.max_workers = max_workers
        self.rate_limit = rate_limit_per_minute
        self.last_request_time = 0
        self.min_interval = 60.0 / rate_limit_per_minute
        
    def process_batch(self, tasks, task_function):
        """Process tasks with controlled parallelism and rate limiting"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {executor.submit(task_function, task): task for task in tasks}
            
            for future in as_completed(future_to_task):
                # Rate limiting
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                
                if time_since_last < self.min_interval:
                    sleep_time = self.min_interval - time_since_last
                    time.sleep(sleep_time + random.uniform(0, 0.1))
                
                self.last_request_time = time.time()
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Task failed: {e}")
        
        return results