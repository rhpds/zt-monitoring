#!/usr/bin/env python3
"""Unit tests for API endpoints"""

import pytest
import aiosqlite
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from api import app, to_sqlite_interval


class TestAPIEndpoints:
    """API endpoint tests"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_root_endpoint_no_database(self):
        """Test root endpoint returns 503 when database connection is unavailable"""
        with patch("api._connection_pool", None):
            response = self.client.get("/")
            assert response.status_code == 503
            assert "Database connection not available" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_root_endpoint_with_database(self):
        """Test root endpoint with database connection"""
        mock_connection = AsyncMock()

        # Create separate mock cursors for each query
        mock_memory_cursor = AsyncMock()
        mock_cpu_cursor = AsyncMock()
        mock_disk_cursor = AsyncMock()
        mock_network_cursor = AsyncMock()

        # Mock memory usage query
        mock_memory_cursor.__aiter__.return_value = [
            {"host": "test-host", "avg_memory": 50.0}
        ]
        mock_memory_cursor.close = AsyncMock()

        # Mock CPU usage query
        mock_cpu_cursor.__aiter__.return_value = [
            {"host": "test-host", "avg_cpu": 25.0}
        ]
        mock_cpu_cursor.close = AsyncMock()

        # Mock disk usage query
        mock_disk_cursor.__aiter__.return_value = [
            {"host": "test-host", "avg_read": 100.0, "avg_write": 200.0}
        ]
        mock_disk_cursor.close = AsyncMock()

        # Mock network usage query
        mock_network_cursor.__aiter__.return_value = [
            {"host": "test-host", "avg_received": 1000.0, "avg_sent": 500.0}
        ]
        mock_network_cursor.close = AsyncMock()

        # Set up the connection mock to return different cursors for different queries
        def execute_side_effect(query, *args):
            if "memory_usage" in query:
                return mock_memory_cursor
            elif "cpu_usage" in query:
                return mock_cpu_cursor
            elif "disk_usage" in query:
                return mock_disk_cursor
            elif "network_usage" in query:
                return mock_network_cursor
            else:
                return AsyncMock()

        mock_connection.execute.side_effect = execute_side_effect

        with patch("api._connection_pool", mock_connection):
            response = self.client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_limit_endpoint_with_time_limit(self):
        """Test limit endpoint with valid time parameter"""
        mock_connection = AsyncMock()

        # Create mock cursors for the limit endpoint
        mock_hosts_cursor = AsyncMock()
        mock_memory_cursor = AsyncMock()
        mock_cpu_cursor = AsyncMock()
        mock_disk_cursor = AsyncMock()
        mock_network_cursor = AsyncMock()

        # Mock the hosts query
        mock_hosts_cursor.__aiter__.return_value = [{"host": "test-host"}]
        mock_hosts_cursor.close = AsyncMock()

        # Mock the individual metric queries
        mock_memory_cursor.fetchone.return_value = {"avg_memory": 50.0}
        mock_memory_cursor.close = AsyncMock()

        mock_cpu_cursor.fetchone.return_value = {"avg_cpu": 25.0}
        mock_cpu_cursor.close = AsyncMock()

        mock_disk_cursor.fetchone.return_value = {"avg_read": 100.0, "avg_write": 200.0}
        mock_disk_cursor.close = AsyncMock()

        mock_network_cursor.fetchone.return_value = {
            "avg_received": 1000.0,
            "avg_sent": 500.0,
        }
        mock_network_cursor.close = AsyncMock()

        # Set up the connection mock to return different cursors for different queries
        def execute_side_effect(query, *args):
            if "DISTINCT host" in query:
                return mock_hosts_cursor
            elif "memory_usage" in query:
                return mock_memory_cursor
            elif "cpu_usage" in query:
                return mock_cpu_cursor
            elif "disk_usage" in query:
                return mock_disk_cursor
            elif "network_usage" in query:
                return mock_network_cursor
            else:
                return AsyncMock()

        mock_connection.execute.side_effect = execute_side_effect

        with patch("api._connection_pool", mock_connection):
            response = self.client.get("/limit/1h")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_limit_endpoint_database_error(self):
        """Test limit endpoint database error handling"""
        mock_connection = AsyncMock()
        mock_connection.execute.side_effect = aiosqlite.Error("Database error")

        with patch("api._connection_pool", mock_connection):
            response = self.client.get("/limit/1h")
            assert response.status_code == 500
            assert "Database error occurred" in response.json()["detail"]

    @pytest.mark.parametrize(
        "time_param,expected_interval",
        [
            ("1s", "-1 seconds"),
            ("30s", "-30 seconds"),
            ("1m", "-1 minutes"),
            ("5m", "-5 minutes"),
            ("1h", "-1 hours"),
            ("2h", "-2 hours"),
            ("1d", "-1 days"),
            ("7d", "-7 days"),
            ("1w", "-1 weeks"),
            ("4w", "-4 weeks"),
        ],
    )
    def test_to_sqlite_interval_valid_formats(self, time_param, expected_interval):
        """Test valid time format conversion"""
        result = to_sqlite_interval(time_param)
        assert result == expected_interval

    @pytest.mark.parametrize(
        "invalid_time",
        [
            "invalid",
            "abc",
            "1hour",
            "1 hour",
            "",
            "1.5h",
            "1h30m",
        ],
    )
    def test_to_sqlite_interval_invalid_formats(self, invalid_time):
        """Test invalid time format handling"""
        with pytest.raises(ValueError, match="Invalid time format"):
            to_sqlite_interval(invalid_time)

    @pytest.mark.parametrize(
        "invalid_unit",
        [
            "1x",
            "1M",
            "3M",
            "1y",
        ],
    )
    def test_to_sqlite_interval_unsupported_units(self, invalid_unit):
        """Test unsupported time units"""
        with pytest.raises(ValueError, match="Unsupported time unit"):
            to_sqlite_interval(invalid_unit)

    def test_limit_endpoint_invalid_time_format(self):
        """Test limit endpoint with invalid time format"""
        # Mock connection so we get to the time format validation
        mock_connection = AsyncMock()
        with patch("api._connection_pool", mock_connection):
            response = self.client.get("/limit/invalid")
            assert response.status_code == 400
            assert "Invalid time format" in response.json()["detail"]

    def test_limit_endpoint_empty_database(self):
        """Test limit endpoint with empty database"""
        mock_connection = AsyncMock()

        # Create mock cursor that returns empty results
        mock_hosts_cursor = AsyncMock()
        mock_hosts_cursor.__aiter__.return_value = []  # No hosts
        mock_hosts_cursor.close = AsyncMock()

        mock_connection.execute.return_value = mock_hosts_cursor

        with patch("api._connection_pool", mock_connection):
            response = self.client.get("/limit/1h")
            assert response.status_code == 200
            data = response.json()
            assert data == {}

    def test_health_endpoint_missing(self):
        """Test that health endpoint returns 404 as it doesn't exist"""
        response = self.client.get("/health")
        assert response.status_code == 404

    def test_large_time_interval(self):
        """Test large time interval handling"""
        mock_connection = AsyncMock()

        # Create mock cursors for the limit endpoint
        mock_hosts_cursor = AsyncMock()
        mock_memory_cursor = AsyncMock()
        mock_cpu_cursor = AsyncMock()
        mock_disk_cursor = AsyncMock()
        mock_network_cursor = AsyncMock()

        # Mock the hosts query
        mock_hosts_cursor.__aiter__.return_value = [{"host": "test-host"}]
        mock_hosts_cursor.close = AsyncMock()

        # Mock the individual metric queries
        mock_memory_cursor.fetchone.return_value = {"avg_memory": 50.0}
        mock_memory_cursor.close = AsyncMock()

        mock_cpu_cursor.fetchone.return_value = {"avg_cpu": 25.0}
        mock_cpu_cursor.close = AsyncMock()

        mock_disk_cursor.fetchone.return_value = {"avg_read": 100.0, "avg_write": 200.0}
        mock_disk_cursor.close = AsyncMock()

        mock_network_cursor.fetchone.return_value = {
            "avg_received": 1000.0,
            "avg_sent": 500.0,
        }
        mock_network_cursor.close = AsyncMock()

        # Set up the connection mock to return different cursors for different queries
        def execute_side_effect(query, *args):
            if "DISTINCT host" in query:
                return mock_hosts_cursor
            elif "memory_usage" in query:
                return mock_memory_cursor
            elif "cpu_usage" in query:
                return mock_cpu_cursor
            elif "disk_usage" in query:
                return mock_disk_cursor
            elif "network_usage" in query:
                return mock_network_cursor
            else:
                return AsyncMock()

        mock_connection.execute.side_effect = execute_side_effect

        with patch("api._connection_pool", mock_connection):
            response = self.client.get("/limit/4w")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        mock_connection = AsyncMock()

        # Create mock cursors for the limit endpoint
        mock_hosts_cursor = AsyncMock()
        mock_memory_cursor = AsyncMock()
        mock_cpu_cursor = AsyncMock()
        mock_disk_cursor = AsyncMock()
        mock_network_cursor = AsyncMock()

        # Mock the hosts query
        mock_hosts_cursor.__aiter__.return_value = [{"host": "test-host"}]
        mock_hosts_cursor.close = AsyncMock()

        # Mock the individual metric queries
        mock_memory_cursor.fetchone.return_value = {"avg_memory": 50.0}
        mock_memory_cursor.close = AsyncMock()

        mock_cpu_cursor.fetchone.return_value = {"avg_cpu": 25.0}
        mock_cpu_cursor.close = AsyncMock()

        mock_disk_cursor.fetchone.return_value = {"avg_read": 100.0, "avg_write": 200.0}
        mock_disk_cursor.close = AsyncMock()

        mock_network_cursor.fetchone.return_value = {
            "avg_received": 1000.0,
            "avg_sent": 500.0,
        }
        mock_network_cursor.close = AsyncMock()

        # Set up the connection mock to return different cursors for different queries
        def execute_side_effect(query, *args):
            if "DISTINCT host" in query:
                return mock_hosts_cursor
            elif "memory_usage" in query:
                return mock_memory_cursor
            elif "cpu_usage" in query:
                return mock_cpu_cursor
            elif "disk_usage" in query:
                return mock_disk_cursor
            elif "network_usage" in query:
                return mock_network_cursor
            else:
                return AsyncMock()

        mock_connection.execute.side_effect = execute_side_effect

        with patch("api._connection_pool", mock_connection):
            response1 = self.client.get("/limit/1h")
            response2 = self.client.get("/limit/1d")

            assert response1.status_code == 200
            assert response2.status_code == 200

    def test_cors_headers(self):
        """Test CORS headers (basic test since no CORS middleware is configured)"""
        response = self.client.options("/limit/1h")
        # Should return 405 since OPTIONS is not implemented for this endpoint
        assert response.status_code == 405

    def test_limit_endpoint_database_exception(self):
        """Test limit endpoint with database exception"""
        mock_connection = AsyncMock()
        mock_connection.execute.side_effect = Exception("Unexpected error")

        with patch("api._connection_pool", mock_connection):
            response = self.client.get("/limit/1h")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/",
            "/limit/1h",
            "/limit/1d",
            "/limit/1w",
        ],
    )
    def test_response_format_consistency(self, endpoint):
        """Test consistent response format across endpoints"""
        mock_connection = AsyncMock()

        # Create separate mock cursors for different query types
        mock_hosts_cursor = AsyncMock()
        mock_memory_cursor = AsyncMock()
        mock_cpu_cursor = AsyncMock()
        mock_disk_cursor = AsyncMock()
        mock_network_cursor = AsyncMock()

        # Set up mocks for root endpoint (uses async for)
        mock_memory_cursor.__aiter__.return_value = [
            {"host": "test-host", "avg_memory": 50.0}
        ]
        mock_memory_cursor.close = AsyncMock()

        mock_cpu_cursor.__aiter__.return_value = [
            {"host": "test-host", "avg_cpu": 25.0}
        ]
        mock_cpu_cursor.close = AsyncMock()

        mock_disk_cursor.__aiter__.return_value = [
            {"host": "test-host", "avg_read": 100.0, "avg_write": 200.0}
        ]
        mock_disk_cursor.close = AsyncMock()

        mock_network_cursor.__aiter__.return_value = [
            {"host": "test-host", "avg_received": 1000.0, "avg_sent": 500.0}
        ]
        mock_network_cursor.close = AsyncMock()

        # Set up mocks for limit endpoints (uses fetchone)
        mock_hosts_cursor.__aiter__.return_value = [{"host": "test-host"}]
        mock_hosts_cursor.close = AsyncMock()

        # For fetchone calls
        mock_memory_cursor.fetchone.return_value = {"avg_memory": 50.0}
        mock_cpu_cursor.fetchone.return_value = {"avg_cpu": 25.0}
        mock_disk_cursor.fetchone.return_value = {"avg_read": 100.0, "avg_write": 200.0}
        mock_network_cursor.fetchone.return_value = {
            "avg_received": 1000.0,
            "avg_sent": 500.0,
        }

        # Set up the connection mock to return different cursors for different queries
        def execute_side_effect(query, *args):
            if "DISTINCT host" in query:
                return mock_hosts_cursor
            elif "memory_usage" in query:
                return mock_memory_cursor
            elif "cpu_usage" in query:
                return mock_cpu_cursor
            elif "disk_usage" in query:
                return mock_disk_cursor
            elif "network_usage" in query:
                return mock_network_cursor
            else:
                return AsyncMock()

        mock_connection.execute.side_effect = execute_side_effect

        with patch("api._connection_pool", mock_connection):
            response = self.client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            # Check that the response format is consistent
            if data:  # If there's data
                for host_data in data.values():
                    assert isinstance(host_data, dict)
