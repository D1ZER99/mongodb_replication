# MongoDB Web Counter - Performance Testing Application

This application is designed for testing MongoDB replication performance and data integrity under different write concern levels and failover scenarios.

## Overview

The web counter application provides a simple HTTP API for incrementing a counter stored in MongoDB. It uses atomic operations (`findOneAndUpdate` with `$inc`) to prevent lost updates in concurrent environments.

## Architecture

```
┌──────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Clients    │  HTTP   │   Flask App      │  pymongo│  MongoDB        │
│ (10 threads) ├────────>│  (Port 8082)     ├────────>│  Replica Set    │
│              │         │  + Waitress WSGI │         │  (3 nodes)      │
└──────────────┘         └──────────────────┘         └─────────────────┘
```

## Files

- **`app_mongodb.py`** - Flask web application with MongoDB backend
- **`client.py`** - HTTP client library for making concurrent requests
- **`test_scenario1_w1.py`** - Test script for write concern w:1
- **`test_scenario2_majority.py`** - Test script for write concern w:majority
- **`test_scenario3_w1_failover.py`** - Test script for w:1 with primary failover
- **`test_scenario4_majority_failover.py`** - Test script for w:majority with primary failover
- **`requirements.txt`** - Python dependencies

## Prerequisites

### System Requirements

- Python 3.8+
- Docker with MongoDB replica set running
- 4GB RAM minimum
- Windows/Linux/macOS

### MongoDB Replica Set

The application requires a MongoDB replica set with 3 nodes:
- mongo1:27017
- mongo2:27017
- mongo3:27017
- Replica set name: `rs0`

See main project README for replica set setup instructions.

## Installation

### 1. Install Python Dependencies

```bash
cd web-counter
pip install -r requirements.txt
```

Required packages:
- Flask==3.0.0 - Web framework
- waitress==3.0.0 - Production WSGI server
- requests==2.31.0 - HTTP client library
- pymongo==4.6.1 - MongoDB driver

### 2. Verify MongoDB Replica Set

Ensure all nodes are running:

```bash
docker ps
```

Expected output should show `mongo1`, `mongo2`, `mongo3` containers.

Check replica set status:

```bash
docker exec -it mongo1 mongosh --eval "rs.status()"
```

## Running the Application

### Start the Web Server

```bash
python app_mongodb.py
```

Expected output:

```
============================================================
Starting MongoDB Web Counter Application
============================================================
MongoDB URI: mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0
Database: counter_db
Collection: counters
============================================================
✓ MongoDB connection successful!
Counter initialized in MongoDB

URL: http://127.0.0.1:8082
============================================================
Server: Waitress (Production WSGI Server)
Threads: 200

Server is ready to accept connections!
Test: Open http://127.0.0.1:8082 in your browser
Press Ctrl+C to stop
```

**Important**: Keep this terminal open while running tests.

### Configuration

#### Environment Variables

```bash
# MongoDB connection string
export MONGO_URI="mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0"

# Default write concern (used if not specified in request)
export WRITE_CONCERN="majority"  # or "1"

python app_mongodb.py
```

#### Connection String Format

The connection string must include all replica set members for automatic failover:

```
mongodb://host1:port1,host2:port2,host3:port3/?replicaSet=rs0
```

This allows the driver to automatically discover and connect to the new primary if the current primary fails.

## API Endpoints

### GET / - Home Page

Returns application status and endpoint information.

```bash
curl http://127.0.0.1:8082
```

Response:
```json
{
  "status": "running",
  "message": "MongoDB Web Counter Application is running!",
  "current_count": 0,
  "database": "MongoDB Replica Set (rs0)",
  "write_concern": "majority",
  "endpoints": {
    "/inc?w=1": "Increment counter with write concern w:1",
    "/inc?w=majority": "Increment counter with write concern w:majority",
    "/count": "Get current count (GET)",
    "/reset": "Reset counter to 0 (POST)"
  }
}
```

### GET/POST /inc - Increment Counter

Atomically increments the counter by 1.

**Parameters**:
- `w` (optional) - Write concern level: "1", "2", "3", or "majority"

**Examples**:

```bash
# Increment with w:1 (fastest)
curl http://127.0.0.1:8082/inc?w=1

# Increment with w:majority (durable)
curl http://127.0.0.1:8082/inc?w=majority

# Increment with default write concern
curl http://127.0.0.1:8082/inc
```

Response: `204 No Content` (for faster processing)

### GET /count - Get Counter Value

Returns the current counter value.

```bash
curl http://127.0.0.1:8082/count
```

Response:
```json
{
  "count": 12345
}
```

### POST /reset - Reset Counter

Resets the counter to 0.

```bash
curl -X POST http://127.0.0.1:8082/reset
```

Response: `204 No Content`

### GET /health - Health Check

Checks if the application and MongoDB connection are healthy.

```bash
curl http://127.0.0.1:8082/health
```

Response:
```json
{
  "status": "healthy",
  "mongodb": "connected"
}
```

## Running Tests

### Test Scenario 1: Write Concern w:1

Tests baseline performance with w:1 (no failover).

```bash
python test_scenario1_w1.py
```

- 10 clients × 10,000 requests = 100,000 total
- Expected: Count = 100,000, fastest performance
- Results saved to: `results_scenario1_w1.txt`

### Test Scenario 2: Write Concern w:majority

Tests performance with w:majority (no failover).

```bash
python test_scenario2_majority.py
```

- 10 clients × 10,000 requests = 100,000 total
- Expected: Count = 100,000, slower than w:1
- Results saved to: `results_scenario2_majority.txt`

### Test Scenario 3: w:1 with Primary Failover

Tests data loss with w:1 during primary failure.

```bash
python test_scenario3_w1_failover.py
```

**Manual steps required**:
1. Start test
2. Wait for 20-30% progress
3. Stop primary node: `docker stop mongo1`
4. Test continues with new primary
5. After test: `docker start mongo1`

- Expected: Count < 100,000 (data loss)
- Results saved to: `results_scenario3_w1_failover.txt`

### Test Scenario 4: w:majority with Primary Failover

Tests NO data loss with w:majority during primary failure.

```bash
python test_scenario4_majority_failover.py
```

**Manual steps required**: Same as Scenario 3

- Expected: Count = 100,000 (NO data loss)
- Results saved to: `results_scenario4_majority_failover.txt`

## Performance Tuning

### Application Configuration

**Connection Pool**:
```python
client = MongoClient(
    MONGO_URI,
    maxPoolSize=100,      # Maximum connections
    minPoolSize=20,       # Minimum kept alive
    maxIdleTimeMS=45000,  # Keep alive time
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000
)
```

**WSGI Server**:
```python
serve(
    app,
    host='0.0.0.0',
    port=8082,
    threads=200,          # Concurrent request handlers
    channel_timeout=60    # Request timeout
)
```

### Client Configuration

**Retry Logic**:
- 3 retries per request
- Exponential backoff (50ms, 100ms, 150ms)
- Handles timeouts and 500 errors

**Session Management**:
- HTTP keep-alive connections
- Connection pooling per client thread

## Troubleshooting

### Application Won't Start

**Error**: `Could not connect to MongoDB`

**Solution**:
```bash
# Check if MongoDB replica set is running
docker ps | grep mongo

# Check replica set status
docker exec -it mongo1 mongosh --eval "rs.status()"

# Restart replica set if needed
docker-compose up -d
```

### Connection Errors During Test

**Error**: `Request timeout after 3 attempts`

**Possible Causes**:
1. MongoDB node is down
2. Network connectivity issues
3. Primary election in progress (during failover tests)

**Solution**:
- Wait 30 seconds for election to complete
- Verify all required nodes are running (2 out of 3 minimum)
- Check Docker network: `docker network inspect mongo-cluster`

### Count Mismatch

**Problem**: Final count doesn't match expected (except Scenario 3)

**Solution**:
```bash
# Check counter directly in MongoDB
docker exec -it mongo1 mongosh

use counter_db
db.counters.findOne({_id: "main_counter"})

# Reset counter and retry
curl -X POST http://127.0.0.1:8082/reset
```

### Port Already in Use

**Error**: `Address already in use: ('0.0.0.0', 8082)`

**Solution**:
```bash
# Windows
netstat -ano | findstr :8082
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8082
kill -9 <PID>

# Or use different port
export PORT=8083
# Modify app_mongodb.py: port=8083
```

## Development

### Adding New Write Concern Levels

Modify the `/inc` endpoint in `app_mongodb.py`:

```python
@app.route('/inc', methods=['GET', 'POST'])
def increment():
    w = request.args.get('w', WRITE_CONCERN)
    
    # Add custom write concern logic
    if w == 'custom':
        write_concern = WriteConcern(w=2, j=True, wtimeout=5000)
    else:
        w = int(w) if w.isdigit() else w
        write_concern = WriteConcern(w=w)
    
    # ...
```

### Custom Test Scenarios

Create new test script based on existing ones:

```python
# test_scenario_custom.py
from client import make_requests_parallel, get_count, reset_counter

BASE_URL = "http://127.0.0.1:8082"
WRITE_CONCERN = "2"  # Custom write concern

# Modify test parameters as needed
REQUESTS_PER_CLIENT = 5000
NUM_CLIENTS = 20
```

## Technical Details

### Atomic Operations

The application uses MongoDB's `findOneAndUpdate()` with `$inc` operator to ensure atomic increments:

```python
counters_with_wc.find_one_and_update(
    {'_id': 'main_counter'},
    {'$inc': {'count': 1}},
    upsert=True
)
```

This prevents lost updates even with high concurrency (no locking needed in application code).

### Write Concern Behavior

**w:1**:
- Write acknowledged by primary only
- Returns immediately
- Risk: Data may not be replicated before primary fails

**w:majority**:
- Write acknowledged by majority of nodes (2 out of 3)
- Waits for replication
- Benefit: Data survives primary failure

### Failover Process

1. Primary node stops
2. Remaining secondaries detect failure (~10 seconds)
3. Election starts (~10-20 seconds)
4. New primary elected
5. Clients automatically discover and reconnect
6. Operations resume

Total failover time: 10-30 seconds

## Contributing

This is educational software for laboratory work. Modifications should maintain:
- Atomic operations for correctness
- Configurable write concerns
- Automatic failover handling
- Clear result reporting

## License

Educational use only - UKU Data Engineering course material.

## Support

For issues or questions:
1. Check this README
2. Review MANUAL_PART2.md for detailed instructions
3. Check MongoDB replica set status
4. Verify network connectivity
5. Review application and MongoDB logs

---

**Quick Start Summary**:

```bash
# 1. Ensure MongoDB replica set is running
docker-compose up -d

# 2. Start web application
cd web-counter
python app_mongodb.py

# 3. Run tests (in new terminal)
python test_scenario1_w1.py
python test_scenario2_majority.py
python test_scenario3_w1_failover.py  # Manual failover required
python test_scenario4_majority_failover.py  # Manual failover required

# 4. Compare results
cat results_scenario*.txt
```
