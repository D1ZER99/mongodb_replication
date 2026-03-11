"""
Web Counter Application with MongoDB on Replica Set
Stores counter in MongoDB cluster for persistence and consistency
"""
from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.write_concern import WriteConcern
import time
import os

app = Flask(__name__)

# MongoDB connection with replica set support
# Connection string includes all replica set members for automatic failover
MONGO_URI = os.getenv('MONGO_URI', "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0")
WRITE_CONCERN = os.getenv('WRITE_CONCERN', 'majority')

client = MongoClient(
    MONGO_URI,
    maxPoolSize=100,  # Increased connection pool for concurrent requests
    minPoolSize=20,
    maxIdleTimeMS=45000,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000
)
db = client['counter_db']
counters = db['counters']

# Initialize counter in MongoDB
def init_counter():
    """Initialize counter document if it doesn't exist"""
    try:
        if counters.count_documents({}) == 0:
            counters.insert_one({'_id': 'main_counter', 'count': 0})
            print("Counter initialized in MongoDB")
        else:
            print(f"Counter already exists with value: {counters.find_one({'_id': 'main_counter'})['count']}")
    except Exception as e:
        print(f"Error initializing counter: {e}")


@app.route('/')
def home():
    """Home page to verify server is running"""
    try:
        counter_doc = counters.find_one({'_id': 'main_counter'})
        current_count = counter_doc['count'] if counter_doc else 0
        
        return jsonify({
            'status': 'running',
            'message': 'MongoDB Web Counter Application is running!',
            'current_count': current_count,
            'database': 'MongoDB Replica Set (rs0)',
            'write_concern': WRITE_CONCERN,
            'endpoints': {
                '/inc?w=1': 'Increment counter with write concern w:1',
                '/inc?w=majority': 'Increment counter with write concern w:majority',
                '/count': 'Get current count (GET)',
                '/reset': 'Reset counter to 0 (POST)'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/inc', methods=['GET', 'POST'])
def increment():
    """Increment the counter by 1 using MongoDB atomic operation"""
    try:
        # Get write concern from query parameter or use environment variable
        w = request.args.get('w', WRITE_CONCERN)
        
        # Convert to appropriate type (int for numbers, string for 'majority')
        if w.isdigit():
            w = int(w)
        
        # Create WriteConcern object
        write_concern = WriteConcern(w=w)
        
        # Use findOneAndUpdate with $inc for atomic increment
        counters_with_wc = counters.with_options(write_concern=write_concern)
        counters_with_wc.find_one_and_update(
            {'_id': 'main_counter'},
            {'$inc': {'count': 1}},
            upsert=True
        )
        return '', 204  # No content response for faster processing
    except PyMongoError as e:
        print(f"MongoDB error: {e}")
        return '', 500


@app.route('/count', methods=['GET'])
def get_count():
    """Get the current counter value from MongoDB"""
    try:
        counter_doc = counters.find_one({'_id': 'main_counter'})
        current_count = counter_doc['count'] if counter_doc else 0
        return jsonify({'count': current_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reset', methods=['POST'])
def reset():
    """Reset the counter to 0 in MongoDB"""
    try:
        counters.update_one(
            {'_id': 'main_counter'},
            {'$set': {'count': 0}},
            upsert=True
        )
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Ping MongoDB to check connection
        client.admin.command('ping')
        return jsonify({'status': 'healthy', 'mongodb': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Starting MongoDB Web Counter Application")
    print("=" * 60)
    print("MongoDB URI:", MONGO_URI)
    print("Database: counter_db")
    print("Collection: counters")
    print("=" * 60)
    
    # Wait for MongoDB to be ready
    max_retries = 10
    for i in range(max_retries):
        try:
            client.admin.command('ping')
            print("✓ MongoDB connection successful!")
            break
        except Exception as e:
            if i < max_retries - 1:
                print(f"Waiting for MongoDB... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"ERROR: Could not connect to MongoDB after {max_retries} attempts")
                print(f"Error: {e}")
                exit(1)
    
    # Initialize counter
    init_counter()
    
    # Create index for better performance
    try:
        counters.create_index([('_id', 1)])
    except Exception as e:
        pass  # Index might already exist
    
    print("\nURL: http://127.0.0.1:8082")
    print("=" * 60)
    
    try:
        from waitress import serve
        print("Server: Waitress (Production WSGI Server)")
        print("Threads: 100")
        print("\nServer is ready to accept connections!")
        print("Test: Open http://127.0.0.1:8082 in your browser")
        print("Press Ctrl+C to stop\n")
        
        # Serve with waitress - optimized for high concurrency
        serve(
            app,
            host='0.0.0.0',
            port=8082,
            threads=200,  # Increased threads for better concurrency
            channel_timeout=60  # Increased timeout for slow requests
        )
    except ImportError:
        print("Server: Flask (Development - Install waitress for better performance)")
        print("\nServer is ready to accept connections!")
        print("Test: Open http://127.0.0.1:8082 in your browser")
        print("Press Ctrl+C to stop\n")
        app.run(host='0.0.0.0', port=8082, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        client.close()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        client.close()
