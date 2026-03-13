"""
Test Scenario 2: Write Concern w:majority
10 clients × 10,000 requests each = 100,000 total
Tests performance with w:majority (slower but more durable)
"""
import time
from client import make_requests_parallel, get_count, reset_counter


BASE_URL = "http://127.0.0.1:8082"
REQUESTS_PER_CLIENT = 10000
NUM_CLIENTS = 10
WRITE_CONCERN = "majority"


def progress_tracker(client_id, completed, total):
    """Print progress updates per client"""
    percentage = (completed / total) * 100
    print(f"Client {client_id}: {completed}/{total} ({percentage:.1f}%)", end='\r')


def run_test():
    """Run Scenario 2: writeConcern w:majority"""
    print("\n" + "="*70)
    print("SCENARIO 2: Write Concern w:majority")
    print("="*70)
    print(f"Configuration:")
    print(f"  - Write Concern: w={WRITE_CONCERN}")
    print(f"  - Number of clients: {NUM_CLIENTS}")
    print(f"  - Requests per client: {REQUESTS_PER_CLIENT:,}")
    print(f"  - Total requests: {NUM_CLIENTS * REQUESTS_PER_CLIENT:,}")
    print(f"  - Expected behavior: Slower writes, majority replica acknowledgment")
    print("="*70)
    
    # Reset counter before test
    print("\n[1/4] Resetting counter...")
    reset_counter(BASE_URL)
    time.sleep(1)
    
    initial_count = get_count(BASE_URL)
    print(f"[2/4] Initial count: {initial_count}")
    
    total_requests = NUM_CLIENTS * REQUESTS_PER_CLIENT
    
    print(f"\n[3/4] Running {total_requests:,} requests with {NUM_CLIENTS} concurrent clients...")
    print("      This will be slower than w:1 due to majority acknowledgment...")
    print("      This may take several minutes...\n")
    
    start_time = time.time()
    elapsed_time = make_requests_parallel(
        BASE_URL, 
        REQUESTS_PER_CLIENT, 
        NUM_CLIENTS,
        write_concern=WRITE_CONCERN,
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
    print("RESULTS - SCENARIO 2")
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
        print("  With w:majority, writes are acknowledged by majority of nodes.")
        print("  Data is durable and safe from single node failures.")
    elif success_rate >= 99:
        print("⚠ Minor data loss detected (< 1%).")
        print("  This is unusual for w:majority without failover.")
    else:
        print("✗ Significant data loss detected!")
        print("  Check if majority of nodes failed during test.")
    
    print(f"\nPerformance: {requests_per_second:.2f} req/s")
    print("This is slower than w:1 but provides stronger durability guarantees.")
    
    return {
        'scenario': 2,
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
    filename = 'results_scenario2_majority.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("MongoDB Replication Performance Testing - Scenario 2\n")
        f.write("="*70 + "\n")
        f.write("Write Concern: w:majority\n")
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
        f.write(f"with {result['clients']} concurrent clients using w:majority.\n\n")
        
        f.write("Key Observations:\n")
        f.write("- w:majority provides durability (writes acknowledged by majority)\n")
        f.write("- Slower than w:1 due to replication wait\n")
        f.write("- Suitable for critical data where consistency is priority\n")
        f.write("- Protects against data loss during primary failure (see Scenario 4)\n")
    
    print(f"\nResults saved to: {filename}")


def main():
    print("\n" + "="*70)
    print("MongoDB Performance Testing - Scenario 2")
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
    print("Scenario 2 Complete!")
    print("="*70)
    print("\nNext: Run Scenario 3 (writeConcern w:1 with failover)")
    print("Command: python test_scenario3_w1_failover.py")


if __name__ == '__main__':
    main()
