"""
Test Scenario 1: Write Concern w:1 (Primary Only)
10 clients × 10,000 requests each = 100,000 total
Tests baseline performance with w:1 (fastest, no replica acknowledgment)
"""
import time
from client import make_requests_parallel, get_count, reset_counter


BASE_URL = "http://127.0.0.1:8082"
REQUESTS_PER_CLIENT = 10000
NUM_CLIENTS = 10
WRITE_CONCERN = "1"


def progress_tracker(client_id, completed, total):
    """Print progress updates per client"""
    percentage = (completed / total) * 100
    print(f"Client {client_id}: {completed}/{total} ({percentage:.1f}%)", end='\r')


def run_test():
    """Run Scenario 1: writeConcern w:1"""
    print("\n" + "="*70)
    print("SCENARIO 1: Write Concern w:1 (Primary Only)")
    print("="*70)
    print(f"Configuration:")
    print(f"  - Write Concern: w={WRITE_CONCERN}")
    print(f"  - Number of clients: {NUM_CLIENTS}")
    print(f"  - Requests per client: {REQUESTS_PER_CLIENT:,}")
    print(f"  - Total requests: {NUM_CLIENTS * REQUESTS_PER_CLIENT:,}")
    print(f"  - Expected behavior: Fast writes, no replica acknowledgment")
    print("="*70)
    
    # Reset counter before test
    print("\n[1/4] Resetting counter...")
    reset_counter(BASE_URL)
    time.sleep(1)
    
    initial_count = get_count(BASE_URL)
    print(f"[2/4] Initial count: {initial_count}")
    
    total_requests = NUM_CLIENTS * REQUESTS_PER_CLIENT
    
    print(f"\n[3/4] Running {total_requests:,} requests with {NUM_CLIENTS} concurrent clients...")
    print("      This may take several minutes...\n")
    
    # Update URL to include write concern parameter
    test_url = f"{BASE_URL}?w={WRITE_CONCERN}"
    
    start_time = time.time()
    elapsed_time = make_requests_parallel(
        test_url, 
        REQUESTS_PER_CLIENT, 
        NUM_CLIENTS, 
        progress_callback=progress_tracker
    )
    
    print("\n\n[4/4] Test completed! Retrieving final count...")
    time.sleep(2)  # Wait for any pending writes
    
    # Get final count
    final_count = get_count(BASE_URL)
    requests_per_second = total_requests / elapsed_time
    
    # Calculate success rate
    expected_count = total_requests
    success_rate = (final_count / expected_count * 100) if expected_count > 0 else 0
    lost_updates = expected_count - final_count
    
    print("\n" + "="*70)
    print("RESULTS - SCENARIO 1")
    print("="*70)
    print(f"Write Concern: w={WRITE_CONCERN}")
    print(f"Number of clients: {NUM_CLIENTS}")
    print(f"Requests per client: {REQUESTS_PER_CLIENT:,}")
    print(f"Total requests sent: {total_requests:,}")
    print(f"Final count in MongoDB: {final_count:,}")
    print(f"Expected count: {expected_count:,}")
    print(f"Lost updates: {lost_updates:,}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Requests per second: {requests_per_second:.2f}")
    print("="*70)
    
    # Analysis
    print("\nANALYSIS:")
    if success_rate >= 99.99:
        print("✓ All requests successfully processed!")
        print("  With w:1, writes are acknowledged immediately by primary.")
        print("  No data loss expected in normal operation (no failover).")
    elif success_rate >= 99:
        print("⚠ Minor data loss detected (< 1%).")
        print("  This is unusual for w:1 without failover.")
    else:
        print("✗ Significant data loss detected!")
        print("  Check if primary failed during test or network issues occurred.")
    
    print(f"\nPerformance: {requests_per_second:.2f} req/s")
    print("This is the baseline performance with w:1 (fastest write concern).")
    
    return {
        'scenario': 1,
        'write_concern': WRITE_CONCERN,
        'clients': NUM_CLIENTS,
        'requests_per_client': REQUESTS_PER_CLIENT,
        'total_requests': total_requests,
        'final_count': final_count,
        'expected_count': expected_count,
        'lost_updates': lost_updates,
        'success_rate': success_rate,
        'time': elapsed_time,
        'requests_per_second': requests_per_second,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }


def save_results(result):
    """Save results to file"""
    filename = 'results_scenario1_w1.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("MongoDB Replication Performance Testing - Scenario 1\n")
        f.write("="*70 + "\n")
        f.write("Write Concern: w:1 (Primary Only)\n")
        f.write("No Primary Failover\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Test Time: {result['timestamp']}\n\n")
        
        f.write(f"Configuration:\n")
        f.write(f"  Write Concern: w={result['write_concern']}\n")
        f.write(f"  Number of clients: {result['clients']}\n")
        f.write(f"  Requests per client: {result['requests_per_client']:,}\n")
        f.write(f"  Total requests sent: {result['total_requests']:,}\n\n")
        
        f.write(f"Results:\n")
        f.write(f"  Final count in MongoDB: {result['final_count']:,}\n")
        f.write(f"  Expected count: {result['expected_count']:,}\n")
        f.write(f"  Lost updates: {result['lost_updates']:,}\n")
        f.write(f"  Success rate: {result['success_rate']:.2f}%\n")
        f.write(f"  Time elapsed: {result['time']:.2f} seconds\n")
        f.write(f"  Requests per second: {result['requests_per_second']:.2f}\n\n")
        
        f.write("-"*70 + "\n")
        f.write("Performance Summary:\n")
        f.write("-"*70 + "\n")
        f.write(f"MongoDB handled {result['requests_per_second']:.2f} requests/second\n")
        f.write(f"with {result['clients']} concurrent clients using w:1.\n\n")
        
        f.write("Key Observations:\n")
        f.write("- w:1 provides fastest performance (writes acknowledged by primary only)\n")
        f.write("- No replica acknowledgment required\n")
        f.write("- Suitable for non-critical data where performance is priority\n")
        f.write("- Risk of data loss during primary failure (see Scenario 3)\n")
    
    print(f"\nResults saved to: {filename}")


def main():
    print("\n" + "="*70)
    print("MongoDB Performance Testing - Scenario 1")
    print("="*70)
    print(f"\nTarget URL: {BASE_URL}")
    print("\nPrerequisites:")
    print("1. MongoDB replica set is running (docker-compose up -d)")
    print("2. All 3 nodes are healthy (docker ps)")
    print("3. Web application is running: python app_mongodb.py")
    print("\nPress Enter to start test or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        return
    
    # Verify server is running
    print("\nVerifying server connection...")
    try:
        count = get_count(BASE_URL)
        print(f"✓ Server is running. Current count: {count}")
    except Exception as e:
        print(f"\n✗ ERROR: Cannot connect to server at {BASE_URL}")
        print(f"Error: {e}")
        print("\nPlease ensure:")
        print("1. MongoDB replica set is running: docker-compose up -d")
        print("2. Server is running: python app_mongodb.py")
        return
    
    # Run test
    result = run_test()
    
    # Save results
    save_results(result)
    
    print("\n" + "="*70)
    print("Scenario 1 Complete!")
    print("="*70)
    print("\nNext: Run Scenario 2 (writeConcern w:majority)")
    print("Command: python test_scenario2_majority.py")


if __name__ == '__main__':
    main()
