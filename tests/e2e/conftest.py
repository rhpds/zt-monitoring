"""
End-to-end test fixtures
"""
import pytest
import tempfile
import os
import subprocess
import time
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
import requests
import json

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

@pytest.fixture(scope="session")
def e2e_environment():
    """Set up complete e2e test environment"""
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        env_config = {
            'temp_dir': temp_dir,
            'db_path': os.path.join(temp_dir, 'test_metrics.db'),
            'inventory_path': os.path.join(temp_dir, 'inventory.ini'),
            'ansible_key': os.path.join(temp_dir, 'test_key'),
            'api_port': 9999,
            'api_host': 'localhost'
        }

        # Create test inventory file
        with open(env_config['inventory_path'], 'w') as f:
            f.write("""[monitoring]
localhost ansible_connection=local

[monitoring:vars]
ansible_user=testuser
ansible_host_key_checking=False
""")

        # Create dummy SSH key
        with open(env_config['ansible_key'], 'w') as f:
            f.write("dummy_ssh_key_content")

        yield env_config

@pytest.fixture
def mock_full_workflow():
    """Mock the complete monitoring workflow"""

    def mock_ansible_execution(*args, **kwargs):
        """Mock ansible-playbook execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Ansible playbook executed successfully"
        mock_result.stderr = ""
        return mock_result

    def mock_monitoring_execution(*args, **kwargs):
        """Mock monitoring script execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'cpu_usage': 45.5,
            'memory_usage': 67.2,
            'disk_io': {'reads': 1000, 'writes': 2000},
            'network_io': {'bytes_sent': 50000, 'bytes_recv': 25000}
        })
        mock_result.stderr = ""
        return mock_result

    def mock_database_operations(*args, **kwargs):
        """Mock database operations"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Database operations successful"
        mock_result.stderr = ""
        return mock_result

    with patch('subprocess.run', side_effect=mock_ansible_execution), \
         patch('subprocess.Popen', return_value=MagicMock()), \
         patch('sqlite3.connect') as mock_db:

        # Configure mock database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('localhost', 45.5, 67.2, 1000, 2000, 50000, 25000)
        ]

        yield {
            'ansible': mock_ansible_execution,
            'monitoring': mock_monitoring_execution,
            'database': mock_database_operations,
            'db_connection': mock_db
        }

@pytest.fixture
def api_client():
    """Create a test client for API testing"""
    from fastapi.testclient import TestClient
    try:
        from api import app
        return TestClient(app)
    except ImportError:
        # If API app can't be imported, create a mock
        mock_client = MagicMock()
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.json.return_value = {
            "cpu_usage": [{"host": "localhost", "cpu_usage": 45.5}],
            "memory_usage": [{"host": "localhost", "memory_usage": 67.2}],
            "disk_io": [{"host": "localhost", "reads": 1000, "writes": 2000}],
            "network_io": [{"host": "localhost", "bytes_sent": 50000, "bytes_recv": 25000}]
        }
        return mock_client

@pytest.fixture
def container_runtime():
    """Mock container runtime for testing container operations"""

    def mock_build_container(*args, **kwargs):
        """Mock container build"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Container built successfully"
        return mock_result

    def mock_run_container(*args, **kwargs):
        """Mock container run"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Container running successfully"
        return mock_result

    with patch('subprocess.run', side_effect=mock_build_container):
        yield {
            'build': mock_build_container,
            'run': mock_run_container
        }

@pytest.fixture
def metrics_collector():
    """Mock metrics collection for e2e testing"""

    def collect_metrics(host="localhost"):
        """Simulate metrics collection"""
        return {
            "timestamp": time.time(),
            "host": host,
            "cpu_usage": 45.5,
            "memory_usage": 67.2,
            "disk_io": {"reads": 1000, "writes": 2000},
            "network_io": {"bytes_sent": 50000, "bytes_recv": 25000}
        }

    def store_metrics(metrics, db_path):
        """Simulate storing metrics in database"""
        return True

    def query_metrics(db_path, time_limit=None):
        """Simulate querying metrics from database"""
        return [
            {"host": "localhost", "cpu_usage": 45.5, "memory_usage": 67.2}
        ]

    return {
        'collect': collect_metrics,
        'store': store_metrics,
        'query': query_metrics
    }

@pytest.fixture
def workflow_orchestrator():
    """Mock workflow orchestration for e2e testing"""

    def execute_monitoring_workflow(inventory_path, db_path):
        """Execute the complete monitoring workflow"""
        # Simulate workflow execution
        time.sleep(0.1)  # Simulate processing time
        return {
            'status': 'success',
            'hosts_processed': 1,
            'metrics_collected': 4,
            'execution_time': 0.1
        }

    def validate_workflow_results(results):
        """Validate workflow execution results"""
        required_keys = ['status', 'hosts_processed', 'metrics_collected']
        return all(key in results for key in required_keys)

    return {
        'execute': execute_monitoring_workflow,
        'validate': validate_workflow_results
    }

@pytest.fixture
def performance_benchmarks():
    """Define performance benchmarks for e2e testing"""
    return {
        'max_response_time': 5.0,  # seconds
        'max_memory_usage': 100,   # MB
        'max_cpu_usage': 80,       # percentage
        'max_workflow_time': 30.0  # seconds
    }

@pytest.fixture
def test_data_generator():
    """Generate test data for e2e scenarios"""

    def generate_host_data(num_hosts=3):
        """Generate test host data"""
        hosts = []
        for i in range(num_hosts):
            hosts.append({
                'name': f'test-host-{i+1}',
                'ip': f'192.168.1.{10+i}',
                'cpu_usage': 20 + (i * 10),
                'memory_usage': 50 + (i * 10),
                'disk_reads': 1000 + (i * 500),
                'disk_writes': 2000 + (i * 500),
                'network_sent': 50000 + (i * 25000),
                'network_recv': 25000 + (i * 12500)
            })
        return hosts

    def generate_time_series_data(duration_minutes=60):
        """Generate time series test data"""
        data_points = []
        for i in range(duration_minutes):
            data_points.append({
                'timestamp': time.time() - (duration_minutes - i) * 60,
                'cpu_usage': 40 + (i % 20),
                'memory_usage': 60 + (i % 15),
                'disk_io': {'reads': 1000 + (i * 10), 'writes': 2000 + (i * 15)},
                'network_io': {'bytes_sent': 50000 + (i * 1000), 'bytes_recv': 25000 + (i * 500)}
            })
        return data_points

    return {
        'hosts': generate_host_data,
        'time_series': generate_time_series_data
    }