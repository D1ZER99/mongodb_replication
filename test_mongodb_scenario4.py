"""
Test Script for MongoDB Web Counter Application
Runs Scenario 4: Ten clients make 10K requests each (100K total)
Saves results to mongodb-web-counter-results.txt
"""
import time
from client import make_requests_parallel, get_count, reset_counter


BASE_URL = "http://127.0.0.1:8082"
REQUESTS_PER_CLIENT = 10000
NUM_CLIENTS = 10


def progress_tracker(completed, total):
    """Print progress updates"""
    percentage = (completed / total) * 100
    print(f"Progress: {completed}/{total} ({percentage:.1f}%) - {completed} requests completed", end='\r')


def run_scenario_4():
    """Scenario 4: Ten clients simultaneously make 10K calls each"""
    print("\n" + "="*60)
    print("MongoDB Web Counter - Scenario 4")
    print("Ten clients, 10K requests each (100K total)")
    print("="*60)
    
    # Reset counter before test
    print("\nResetting counter...")
    reset_counter(BASE_URL)
    time.sleep(1)  # Wait for reset to complete
    
    initial_count = get_count(BASE_URL)
    print(f"Initial count: {initial_count}")
    
    total_requests = NUM_CLIENTS * REQUESTS_PER_CLIENT
    
    print(f"\nRunning {total_requests:,} requests with {NUM_CLIENTS} concurrent clients...")
    print("This may take several minutes...\n")
    
    start_time = time.time()
    elapsed_time = make_requests_parallel(
        BASE_URL, 
        REQUESTS_PER_CLIENT, 
        NUM_CLIENTS, 
        progress_callback=progress_tracker
    )
    end_time = time.time()
    
    print()  # New line after progress
    print("\nTest completed! Retrieving final count...")
    
    # Get final count
    final_count = get_count(BASE_URL)
    requests_per_second = total_requests / elapsed_time
    
    # Calculate success rate
    expected_count = total_requests
    success_rate = (final_count / expected_count * 100) if expected_count > 0 else 0
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Number of clients: {NUM_CLIENTS}")
    print(f"Requests per client: {REQUESTS_PER_CLIENT:,}")
    print(f"Total requests sent: {total_requests:,}")
    print(f"Final count in MongoDB: {final_count:,}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Requests per second: {requests_per_second:.2f}")
    print("="*60)
    
    return {
        'scenario': 4,
        'clients': NUM_CLIENTS,
        'requests_per_client': REQUESTS_PER_CLIENT,
        'total_requests': total_requests,
        'final_count': final_count,
        'expected_count': expected_count,
        'success_rate': success_rate,
        'time': elapsed_time,
        'requests_per_second': requests_per_second,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)),
        'end_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    }


def save_results(result):
    """Save results to mongodb-web-counter-results.txt"""
    filename = 'mongodb-web-counter-results.txt'
    
    with open(filename, 'w') as f:
        f.write("MongoDB Web Counter Application - Performance Test Results\n")
        f.write("="*60 + "\n")
        f.write("Scenario 4: Ten Clients with 10K Requests Each\n")
        f.write("Database: MongoDB Replica Set (rs0)\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Test Start Time: {result['start_time']}\n")
        f.write(f"Test End Time: {result['end_time']}\n\n")
        
        f.write(f"Configuration:\n")
        f.write(f"  Number of clients: {result['clients']}\n")
        f.write(f"  Requests per client: {result['requests_per_client']:,}\n")
        f.write(f"  Total requests sent: {result['total_requests']:,}\n\n")
        
        f.write(f"Results:\n")
        f.write(f"  Final count in MongoDB: {result['final_count']:,}\n")
        f.write(f"  Expected count: {result['expected_count']:,}\n")
        f.write(f"  Success rate: {result['success_rate']:.2f}%\n")
        f.write(f"  Time elapsed: {result['time']:.2f} seconds\n")
        f.write(f"  Requests per second: {result['requests_per_second']:.2f}\n\n")
        
        f.write("-"*60 + "\n")
        f.write("Performance Summary:\n")
        f.write("-"*60 + "\n")
        f.write(f"MongoDB handled {result['requests_per_second']:.2f} requests/second\n")
        f.write(f"with {result['clients']} concurrent clients.\n\n")
        
        if result['success_rate'] >= 99.9:
            f.write("✓ All requests were successfully processed!\n")
        elif result['success_rate'] >= 95:
            f.write("⚠ Most requests were processed, but some may have been lost.\n")
        else:
            f.write("✗ Significant data loss detected. Check MongoDB logs.\n")
    
    print(f"\nResults saved to: {filename}")


def main():
    print("\n" + "="*60)
    print("MongoDB Web Counter - Performance Testing")
    print("="*60)
    print(f"\nTarget URL: {BASE_URL}")
    print("Make sure:")
    print("1. MongoDB replica set is running (docker ps)")
    print("2. Web application is running: python app_mongodb.py")
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
        print("1. MongoDB is running: docker ps | grep mongodb")
        print("2. Server is running: python app_mongodb.py")
        return
    
    # Run scenario 4
    result = run_scenario_4()
    
    # Save results
    save_results(result)
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)


if __name__ == '__main__':
    main()
