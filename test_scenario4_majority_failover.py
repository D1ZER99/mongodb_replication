"""
Test Scenario 4: Write Concern w:majority with Primary Failover
10 clients × 10,000 requests each = 100,000 total
Tests NO data loss with w:majority when primary fails during operation
MANUAL INTERVENTION REQUIRED: You must stop the primary node during test
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
    """Run Scenario 4: writeConcern w:majority with failover"""
    print("\n" + "="*70)
    print("SCENARIO 4: Write Concern w:majority WITH PRIMARY FAILOVER")
    print("="*70)
    print(f"Configuration:")
    print(f"  - Write Concern: w={WRITE_CONCERN}")
    print(f"  - Number of clients: {NUM_CLIENTS}")
    print(f"  - Requests per client: {REQUESTS_PER_CLIENT:,}")
    print(f"  - Total requests: {NUM_CLIENTS * REQUESTS_PER_CLIENT:,}")
    print(f"  - Expected behavior: NO data loss (majority acknowledgment)")
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
    print("   - NO writes should be lost (all were majority-acknowledged)")
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
    time.sleep(3)  # Wait for any pending writes
    
    # Get final count
    final_count = get_count(BASE_URL)
    requests_per_second = total_requests / elapsed_time
    
    # Calculate success rate
    expected_count = total_requests
    success_rate = (final_count / expected_count * 100) if expected_count > 0 else 0
    lost_updates = expected_count - final_count
    
    print("\n" + "="*70)
    print("RESULTS - SCENARIO 4")
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
    if success_rate >= 99.9:
        print(f"✓ Expected behavior: NO data loss (or minimal < 0.1%)")
        print("  With w:majority, writes are acknowledged only after replication")
        print("  to majority of nodes. Failover does not cause data loss.")
        print(f"  Lost updates: {lost_updates:,} (should be 0 or very few)")
    elif lost_updates > 0:
        print(f"⚠ Some data loss detected: {lost_updates:,} updates lost")
        print("  This is unexpected with w:majority.")
        print("  Possible causes:")
        print("  - Network issues during test")
        print("  - Multiple nodes failed")
        print("  - Clients timed out and didn't retry")
    else:
        print("⚠ Did you stop the primary node during the test?")
        print("  If not, try running again and stop primary at 20-30% progress.")
    
    print(f"\nPerformance: {requests_per_second:.2f} req/s")
    print("Performance includes failover time (~10-30 seconds for election).")
    print("Note: w:majority is slower than w:1 but provides data durability.")
    
    print("\nREMINDER: Restart the stopped node if you haven't already:")
    print("  docker start mongo1  (or mongo2/mongo3 depending on which was primary)")
    
    return {
        'scenario': 4,
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
    filename = 'results_scenario4_majority_failover.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("MongoDB Replication Performance Testing - Scenario 4\n")
        f.write("="*70 + "\n")
        f.write("Write Concern: w:majority\n")
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
        if result['lost_updates'] > 0:
            f.write(f"  Loss rate: {100 - result['success_rate']:.2f}%\n")
        f.write(f"  Time elapsed: {result['time']:.2f} seconds\n")
        f.write(f"  Requests per second: {result['requests_per_second']:.2f}\n\n")
        
        f.write("-"*70 + "\n")
        f.write("Performance Summary:\n")
        f.write("-"*70 + "\n")
        f.write(f"MongoDB handled {result['requests_per_second']:.2f} requests/second\n")
        f.write(f"with {result['clients']} concurrent clients using w:majority.\n")
        f.write(f"Primary failover occurred during test.\n\n")
        
        f.write("Key Observations:\n")
        if result['lost_updates'] == 0:
            f.write("- ✓ NO data loss with w:majority during failover!\n")
        else:
            f.write(f"- {result['lost_updates']:,} updates were lost (unexpected)\n")
        f.write("- w:majority ensures writes are replicated before acknowledgment\n")
        f.write("- Committed writes survive primary failure\n")
        f.write("- Clients automatically reconnected to new primary\n")
        f.write("- Recommended for critical data requiring durability\n")
        f.write("\nComparison with Scenario 3 (w:1):\n")
        f.write("- w:majority: Slower but NO data loss during failover\n")
        f.write("- w:1: Faster but data loss possible during failover\n")
        f.write("- Trade-off: Performance vs. Durability\n")
    
    print(f"\nResults saved to: {filename}")


def main():
    print("\n" + "="*70)
    print("MongoDB Performance Testing - Scenario 4")
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
        print("ALL SCENARIOS COMPLETE!")
        print("="*70)
        print("\nYou have completed all 4 performance test scenarios:")
        print("  ✓ Scenario 1: w:1 (baseline performance)")
        print("  ✓ Scenario 2: w:majority (durability)")
        print("  ✓ Scenario 3: w:1 with failover (data loss)")
        print("  ✓ Scenario 4: w:majority with failover (NO data loss)")
        print("\nCompare all results files to analyze performance vs. durability trade-offs!")


if __name__ == '__main__':
    main()
