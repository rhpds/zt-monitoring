"""
Integration test fixtures
"""

import pytest
import tempfile
import os
import sqlite3
import subprocess
import time
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="module")
def integration_db():
    """Create a test database with schema and sample data for integration tests"""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Create database schema using the same commands from entrypoint.sh
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cpu_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cpu_usage REAL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            memory_usage REAL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS disk_io (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reads REAL,
            writes REAL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS network_io (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bytes_sent REAL,
            bytes_recv REAL
        )
    """
    )

    # Insert sample data for testing
    test_data = [
        ("test-host-1", 25.5, 60.2, 1000, 2000, 50000, 25000),
        ("test-host-2", 45.8, 78.3, 1500, 2500, 75000, 35000),
        ("test-host-3", 30.1, 55.7, 1200, 2200, 60000, 30000),
    ]

    for host, cpu, memory, disk_r, disk_w, net_s, net_r in test_data:
        cursor.execute(
            "INSERT INTO cpu_usage (host, cpu_usage) VALUES (?, ?)", (host, cpu)
        )
        cursor.execute(
            "INSERT INTO memory_usage (host, memory_usage) VALUES (?, ?)",
            (host, memory),
        )
        cursor.execute(
            "INSERT INTO disk_io (host, reads, writes) VALUES (?, ?, ?)",
            (host, disk_r, disk_w),
        )
        cursor.execute(
            "INSERT INTO network_io (host, bytes_sent, bytes_recv) VALUES (?, ?, ?)",
            (host, net_s, net_r),
        )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_ansible_runner():
    """Mock ansible runner for testing"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Ansible executed successfully"
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_monitoring_script():
    """Mock monitoring script execution"""

    def mock_monitoring_output():
        return '{"cpu_usage": 45.5, "memory_usage": 67.2, "disk_io": {"reads": 1000, "writes": 2000}, "network_io": {"bytes_sent": 50000, "bytes_recv": 25000}}'

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_monitoring_output()
        yield mock_run


@pytest.fixture
def temp_inventory_file():
    """Create a temporary Ansible inventory file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        f.write(
            """[monitoring]
test-host-1 ansible_host=192.168.1.10
test-host-2 ansible_host=192.168.1.11
test-host-3 ansible_host=192.168.1.12

[monitoring:vars]
ansible_user=testuser
ansible_ssh_private_key_file=/tmp/test_key
ansible_host_key_checking=False
"""
        )
        f.flush()
        inventory_path = f.name

    yield inventory_path

    # Cleanup
    if os.path.exists(inventory_path):
        os.unlink(inventory_path)


@pytest.fixture
def mock_container_environment():
    """Mock container environment variables"""
    env_vars = {
        "DB_PATH": "/tmp/test_metrics.db",
        "ANSIBLE_INVENTORY": "localhost,",
        "ANSIBLE_REMOTE_USER": "testuser",
        "ANSIBLE_PRIVATE_KEY_FILE": "/tmp/test_key",
        "ANSIBLE_HOST_KEY_CHECKING": "False",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def api_server_process():
    """Start API server process for integration testing"""
    # This would start the actual API server in a subprocess
    # For now, we'll mock it since we don't want to start real servers in tests
    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_process.returncode = None

    with patch("subprocess.Popen", return_value=mock_process):
        yield mock_process


@pytest.fixture
def performance_timer():
    """Time test execution for performance testing"""
    start_time = time.time()
    yield
    end_time = time.time()
    execution_time = end_time - start_time

    # You can add assertions here for performance requirements
    # For example: assert execution_time < 5.0, "Test took too long"
    print(f"Test execution time: {execution_time:.2f} seconds")
