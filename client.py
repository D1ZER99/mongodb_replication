"""
HTTP Client Module
Makes concurrent requests to the web counter application
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def make_request(session, url, max_retries=10):
    """Make a single HTTP request using a session with retry logic"""
    for attempt in range(max_retries):
        try:
            response = session.post(url, timeout=10)  # Increased for failover scenarios
            if response.status_code in (204, 200):
                return True
            elif response.status_code == 500 and attempt < max_retries - 1:
                # Server error, retry with backoff
                time.sleep(0.1 * (attempt + 1))  # Increased backoff for failover
                continue
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # Increased backoff
                continue
            print(f"\nRequest timeout after {max_retries} attempts")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # Increased backoff
                continue
            print(f"\nRequest failed after {max_retries} attempts: {e}")
    return False


def make_requests_sequential(base_url, num_requests, write_concern=None, progress_callback=None):
    """Make requests sequentially from a single client"""
    # Construct URL with query parameter if write_concern is specified
    if write_concern:
        url = f"{base_url}/inc?w={write_concern}"
    else:
        url = f"{base_url}/inc"
    
    start_time = time.time()
    
    # Use session for connection pooling with keep-alive
    with requests.Session() as session:
        # Simple configuration - let requests handle connection pooling
        session.headers.update({'Connection': 'keep-alive'})
        
        for i in range(num_requests):
            success = make_request(session, url)
            # Track failures but continue - retries are handled in make_request
            if progress_callback and (i + 1) % 1000 == 0:
                progress_callback(i + 1, num_requests)
    
    end_time = time.time()
    return end_time - start_time


def make_requests_parallel(base_url, num_requests, num_clients, write_concern=None, progress_callback=None):
    """
    Make requests in parallel using multiple clients
    Each client makes (num_requests) requests
    """
    # Construct URL with query parameter if write_concern is specified
    if write_concern:
        url = f"{base_url}/inc?w={write_concern}"
    else:
        url = f"{base_url}/inc"
    
    start_time = time.time()
    
    def client_worker(client_id, num_reqs):
        """Each client uses its own session"""
        with requests.Session() as session:
            # Simple configuration - let requests handle connection pooling
            session.headers.update({'Connection': 'keep-alive'})
            
            for i in range(num_reqs):
                success = make_request(session, url)
                # Track failures but continue - retries are handled in make_request
                # Progress tracking per client (no lock needed)
                if progress_callback and (i + 1) % 1000 == 0:
                    progress_callback(client_id, i + 1, num_reqs)
    
    # Use ThreadPoolExecutor to simulate multiple clients
    with ThreadPoolExecutor(max_workers=num_clients) as executor:
        futures = [executor.submit(client_worker, i, num_requests) for i in range(num_clients)]
        
        # Wait for all clients to complete
        for future in as_completed(futures):
            future.result()
    
    end_time = time.time()
    return end_time - start_time


def get_count(base_url):
    """Get the current counter value"""
    try:
        response = requests.get(f"{base_url}/count", timeout=5)
        if response.status_code == 200:
            return response.json()['count']
    except Exception as e:
        print(f"Failed to get count: {e}")
    return None


def reset_counter(base_url):
    """Reset the counter to 0"""
    try:
        response = requests.post(f"{base_url}/reset", timeout=5)
        return response.status_code == 204
    except Exception as e:
        print(f"Failed to reset counter: {e}")
        return False
