"""
Test Scenario 3: Write Concern w:1 with Primary Failover
10 clients × 10,000 requests each = 100,000 total
Tests data loss with w:1 when primary fails during operation
MANUAL INTERVENTION REQUIRED: You must stop the primary node during test
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
    """Run Scenario 3: writeConcern w:1 with failover"""
    print("\n" + "="*70)
    print("SCENARIO 3: Write Concern w:1 WITH PRIMARY FAILOVER")
    print("="*70)
    print(f"Configuration:")
    print(f"  - Write Concern: w={WRITE_CONCERN}")
    print(f"  - Number of clients: {NUM_CLIENTS}")
    print(f"  - Requests per client: {REQUESTS_PER_CLIENT:,}")
    print(f"  - Total requests: {NUM_CLIENTS * REQUESTS_PER_CLIENT:,}")
    print(f"  - Expected behavior: Data loss possible when primary fails")
    print("="*70)
    
    print("\n" + "!"*70)
    print("IMPORTANT - MANUAL INTERVENTION REQUIRED")
    print("!"*70)
    print("\nDuring this test, you must manually stop the PRIMARY node:")
    print("\n1. Open a NEW terminal window")
    print("2. Wait for test to start and show progress (around 20-30% completion)")
    print("3. Find the current primary node:")
    print("   docker exec -it mongo1 mongosh --eval 'rs.isMaster().primary'")
    print("\n4. Stop the primary node (if mongo1 is primary):")
    print("   docker stop mongo1")
    print("\n5. Observe:")
    print("   - Clients will get errors temporarily")
    print("   - After ~10-30 seconds, new primary will be elected")
    print("   - Clients will reconnect and continue")
    print("   - Some writes on old primary will be LOST (not replicated)")
    print("\n6. After test completes, restart the stopped node:")
    print("   docker start mongo1")
    print("\n" + "!"*70)
    print("\nPress Enter when you understand the instructions...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        return None
    
    # Reset counter before test
    print("\n[1/4] Resetting counter...")
    reset_counter(BASE_URL)
    time.sleep(1)
    
    initial_count = get_count(BASE_URL)
    print(f"[2/4] Initial count: {initial_count}")
    
    total_requests = NUM_CLIENTS * REQUESTS_PER_CLIENT
    
    print(f"\n[3/4] Starting test with {total_requests:,} requests...")
    print("\n" + "*"*70)
    print("*** NOW: WAIT FOR PROGRESS TO REACH 20-30%, THEN STOP PRIMARY NODE ***")
    print("*"*70 + "\n")
    
    start_time = time.time()
    elapsed_time = make_requests_parallel(
        BASE_URL, 
        REQUESTS_PER_CLIENT, 
        NUM_CLIENTS,
        write_concern=WRITE_CONCERN,
        progress_callback=progress_tracker
    )
    
    print("\n\n[4/4] Test completed! Retrieving final count...")
    time.sleep(3)  # Wait for any pending writes
    
    # Get final count
    final_count = get_count(BASE_URL)
    requests_per_second = total_requests / elapsed_time
    
    # Calculate success rate
    expected_count = total_requests
    success_rate = (final_count / expected_count * 100) if expected_count > 0 else 0
    lost_updates = expected_count - final_count
    
    print("\n" + "="*70)
    print("RESULTS - SCENARIO 3")
    print("="*70)
    print(f"Write Concern: w={WRITE_CONCERN}")
    print(f"Failover: PRIMARY NODE STOPPED DURING TEST")
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
    if lost_updates > 0:
        print(f"✓ Expected behavior observed: {lost_updates:,} updates lost")
        print("  With w:1, writes acknowledged by primary may not be replicated")
        print("  before failover. These writes are lost during rollback.")
        print(f"  Loss rate: {(lost_updates/expected_count*100):.2f}%")
    else:
        print("⚠ No data loss detected - did you stop the primary node?")
        print("  Try running the test again and ensure you stop the primary")
        print("  during active writes (20-30% progress).")
    
    print(f"\nPerformance: {requests_per_second:.2f} req/s")
    print("Performance includes failover time (~10-30 seconds for election).")
    
    print("\nREMINDER: Restart the stopped node if you haven't already:")
    print("  docker start mongo1  (or mongo2/mongo3 depending on which was primary)")
    
    return {
        'scenario': 3,
        'write_concern': WRITE_CONCERN,
        'failover': True,
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
    filename = 'results_scenario3_w1_failover.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("MongoDB Replication Performance Testing - Scenario 3\n")
        f.write("="*70 + "\n")
        f.write("Write Concern: w:1 (Primary Only)\n")
        f.write("WITH PRIMARY FAILOVER DURING TEST\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Test Time: {result['timestamp']}\n\n")
        
        f.write(f"Configuration:\n")
        f.write(f"  Write Concern: w={result['write_concern']}\n")
        f.write(f"  Failover: Yes (primary stopped during test)\n")
        f.write(f"  Number of clients: {result['clients']}\n")
        f.write(f"  Requests per client: {result['requests_per_client']:,}\n")
        f.write(f"  Total requests sent: {result['total_requests']:,}\n\n")
        
        f.write(f"Results:\n")
        f.write(f"  Final count in MongoDB: {result['final_count']:,}\n")
        f.write(f"  Expected count: {result['expected_count']:,}\n")
        f.write(f"  Lost updates: {result['lost_updates']:,}\n")
        f.write(f"  Success rate: {result['success_rate']:.2f}%\n")
        f.write(f"  Loss rate: {100 - result['success_rate']:.2f}%\n")
        f.write(f"  Time elapsed: {result['time']:.2f} seconds\n")
        f.write(f"  Requests per second: {result['requests_per_second']:.2f}\n\n")
        
        f.write("-"*70 + "\n")
        f.write("Performance Summary:\n")
        f.write("-"*70 + "\n")
        f.write(f"MongoDB handled {result['requests_per_second']:.2f} requests/second\n")
        f.write(f"with {result['clients']} concurrent clients using w:1.\n")
        f.write(f"Primary failover occurred during test.\n\n")
        
        f.write("Key Observations:\n")
        f.write(f"- {result['lost_updates']:,} updates were lost during failover\n")
        f.write("- w:1 acknowledges writes before replication\n")
        f.write("- Uncommitted writes on failed primary are rolled back\n")
        f.write("- Clients automatically reconnected to new primary\n")
        f.write("- Use w:majority for critical data (see Scenario 4)\n")
    
    print(f"\nResults saved to: {filename}")


def main():
    print("\n" + "="*70)
    print("MongoDB Performance Testing - Scenario 3")
    print("="*70)
    print(f"\nTarget URL: {BASE_URL}")
    print("\nPrerequisites:")
    print("1. MongoDB replica set is running (docker-compose up -d)")
    print("2. All 3 nodes are healthy (docker ps)")
    print("3. Web application is running: python app_mongodb.py")
    print("4. You have a SECOND terminal ready to stop the primary node")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
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
    
    if result:
        # Save results
        save_results(result)
        
        print("\n" + "="*70)
        print("Scenario 3 Complete!")
        print("="*70)
        print("\nNext: Run Scenario 4 (writeConcern w:majority with failover)")
        print("Command: python test_scenario4_majority_failover.py")


if __name__ == '__main__':
    main()
