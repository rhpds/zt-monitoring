#!/bin/bash
# Set the path to your SQLite database
DB_PATH="/tmp/metrics.db"
cd /app/

if [ ! -x ${DB_PATH} ]; then
# Create the database and tables
sqlite3 $DB_PATH <<EOF
CREATE TABLE IF NOT EXISTS cpu_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cpu_usage REAL
);

CREATE TABLE IF NOT EXISTS memory_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    memory_usage REAL
);

CREATE TABLE IF NOT EXISTS disk_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read REAL,
    write REAL
);

CREATE TABLE IF NOT EXISTS network_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received REAL,
    sent REAL
);
EOF
fi

# Set default values for watch interval and timeout
WATCH_INTERVAL=${WATCH_INTERVAL:-5}
TIMEOUT_SECONDS=${TIMEOUT_SECONDS:-4}

# Start FastAPI server in background
fastapi dev --host 0.0.0.0 --port 9999 api.py &

# Function to handle graceful shutdown
cleanup() {
    echo "Received shutdown signal, stopping..."
    # Kill background processes
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

# Set up signal trapping for graceful shutdown
trap cleanup SIGTERM SIGINT SIGQUIT

# Run periodic task using a simple loop instead of watch
while true; do
    echo "Running ansible playbook at $(date)"

    # Run with timeout and handle failure gracefully
    if timeout ${TIMEOUT_SECONDS} ansible-playbook main.yml; then
        echo "Playbook completed successfully"
    else
        echo "Playbook timed out or failed"
    fi

    # Sleep for the specified interval
    sleep ${WATCH_INTERVAL}
done
