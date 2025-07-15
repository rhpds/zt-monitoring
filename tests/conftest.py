"""
Shared fixtures for all test types
"""
import pytest
import tempfile
import os
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Generator, Any

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary database file for testing"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    # Create database schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cpu_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cpu_usage REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            memory_usage REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disk_io (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reads REAL,
            writes REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_io (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bytes_sent REAL,
            bytes_recv REAL
        )
    ''')

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_proc_files():
    """Mock system /proc files for testing"""
    return {
        'stat': "cpu  123456 0 654321 999999 0 0 0 0 0 0\n",
        'meminfo': """MemTotal:        8000000 kB
MemFree:         2000000 kB
MemAvailable:    4000000 kB
Buffers:          500000 kB
Cached:          1500000 kB
""",
        'diskstats': """   8       0 sda 1000 0 0 0 2000 0 0 0 0 0 0 0 0 0 0 0 0
   8       1 sda1 100 0 0 0 200 0 0 0 0 0 0 0 0 0 0 0 0
""",
        'netdev': """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:    1000     100    0    0    0     0          0         0     1000     100    0    0    0     0       0          0
  eth0:   50000     500    0    0    0     0          0         0    25000     250    0    0    0     0       0          0
"""
    }


@pytest.fixture(autouse=True)
def mock_external_calls(request):
    """Mock external calls by default to prevent side effects"""

    # Skip mocking for specific integration tests that need real subprocess
    if (hasattr(request, 'node') and
        hasattr(request.node, 'name') and
        request.node.name in ['test_monitoring_script_execution', 'test_performance_metrics']):
        yield {}
        return

    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('subprocess.run') as mock_subprocess:

        # Configure default mock responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok"}

        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "success"

        yield {
            'requests_get': mock_get,
            'requests_post': mock_post,
            'subprocess_run': mock_subprocess
        }


@pytest.fixture
def sample_metrics():
    """Sample metrics data for testing"""
    return {
        'cpu_usage': [
            {'host': 'test-host-1', 'cpu_usage': 25.5},
            {'host': 'test-host-2', 'cpu_usage': 45.2},
        ],
        'memory_usage': [
            {'host': 'test-host-1', 'memory_usage': 60.8},
            {'host': 'test-host-2', 'memory_usage': 78.9},
        ],
        'disk_io': [
            {'host': 'test-host-1', 'reads': 1000.0, 'writes': 2000.0},
            {'host': 'test-host-2', 'reads': 1500.0, 'writes': 2500.0},
        ],
        'network_io': [
            {'host': 'test-host-1', 'bytes_sent': 50000.0, 'bytes_recv': 25000.0},
            {'host': 'test-host-2', 'bytes_sent': 75000.0, 'bytes_recv': 35000.0},
        ]
    }


@pytest.fixture
def mock_ansible_environment():
    """Mock Ansible environment variables"""
    env_vars = {
        'ANSIBLE_HOST_KEY_CHECKING': 'False',
        'ANSIBLE_SSH_RETRIES': '3',
        'ANSIBLE_TIMEOUT': '10',
        'ANSIBLE_INVENTORY': 'localhost,',
        'ANSIBLE_REMOTE_USER': 'test',
        'ANSIBLE_PRIVATE_KEY_FILE': '/tmp/test_key',
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def temp_work_dir():
    """Create a temporary working directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_cwd)


@pytest.fixture
def mock_time():
    """Mock time-related functions for consistent testing"""
    with patch('time.time') as mock_time_time, \
         patch('time.sleep') as mock_time_sleep:

        mock_time_time.return_value = 1234567890.0
        mock_time_sleep.return_value = None

        yield {
            'time': mock_time_time,
            'sleep': mock_time_sleep
        }