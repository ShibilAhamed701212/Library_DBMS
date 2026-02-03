import time
import threading
from collections import defaultdict

class RateLimiter:
    """
    In-Memory Rate Limiter using Token Bucket / Sliding Window.
    """
    def __init__(self):
        # Key -> (tokens, last_refill)
        self.buckets = defaultdict(lambda: (5, time.time())) 
        self.lock = threading.Lock()
        
        # Rate: 5 requests per 2 seconds
        self.rate = 5
        self.per = 2.0 

    def check(self, key):
        with self.lock:
            now = time.time()
            tokens, last_refill = self.buckets[key]
            
            # Refill
            elapsed = now - last_refill
            refill = int(elapsed * (self.rate / self.per))
            
            if refill > 0:
                tokens = min(self.rate, tokens + refill)
                last_refill = now
            
            # Consume
            if tokens >= 1:
                self.buckets[key] = (tokens - 1, last_refill)
                return True
            else:
                self.buckets[key] = (tokens, last_refill)
                return False

rate_limiter = RateLimiter()

def check_rate_limit(key):
    return rate_limiter.check(key)
