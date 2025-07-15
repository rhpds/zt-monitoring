#!/usr/bin/env python3
"""Unit tests for monitoring functions"""

import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
from monitoring import (
    get_cpu_usage,
    get_memory_usage,
    get_disk_io,
    get_network_io,
    main,
    PSUTIL_AVAILABLE,
)


class TestMonitoring:
    """Monitoring function tests"""

    def test_get_cpu_usage_without_psutil(self):
        """Test CPU usage retrieval without psutil"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            with patch(
                "builtins.open", mock_open(read_data="cpu  100 0 50 25 0 0 0 0 0 0\n")
            ):
                with patch("time.sleep"):
                    # Mock the second read
                    with patch(
                        "builtins.open",
                        mock_open(read_data="cpu  200 0 100 50 0 0 0 0 0 0\n"),
                    ):
                        cpu_usage = get_cpu_usage()
                        assert isinstance(cpu_usage, float)
                        assert cpu_usage >= 0

    def test_get_memory_usage_without_psutil(self):
        """Test memory usage retrieval without psutil"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            meminfo_data = """MemTotal:        8000000 kB
MemFree:         2000000 kB
MemAvailable:    3000000 kB
Buffers:          500000 kB
Cached:          1000000 kB
"""
            with patch("builtins.open", mock_open(read_data=meminfo_data)):
                memory_usage = get_memory_usage()
                assert isinstance(memory_usage, float)
                assert memory_usage >= 0

    def test_get_disk_io_without_psutil(self):
        """Test disk I/O retrieval without psutil"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            diskstats_data = """   8       0 sda 1000 0 0 0 2000 0 0 0 0 0 0 0 0 0 0 0 0
   8       1 sda1 500 0 0 0 1000 0 0 0 0 0 0 0 0 0 0 0 0
"""
            with patch("builtins.open", mock_open(read_data=diskstats_data)):
                disk_io = get_disk_io()
                assert isinstance(disk_io, tuple)
                assert len(disk_io) == 2
                assert isinstance(disk_io[0], int)  # reads
                assert isinstance(disk_io[1], int)  # writes

    def test_get_network_io_without_psutil(self):
        """Test network I/O retrieval without psutil"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            net_dev_data = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: 1000000    1000    0    0    0     0          0         0  1000000    1000    0    0    0     0       0          0
  eth0: 5000000    5000    0    0    0     0          0         0  3000000    3000    0    0    0     0       0          0
"""
            with patch("builtins.open", mock_open(read_data=net_dev_data)):
                network_io = get_network_io()
                assert isinstance(network_io, tuple)
                assert len(network_io) == 2
                assert isinstance(network_io[0], int)  # bytes_recv
                assert isinstance(network_io[1], int)  # bytes_sent

    def test_get_cpu_usage_file_not_found(self):
        """Test CPU usage when /proc/stat is not accessible"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            with patch("builtins.open", side_effect=IOError("File not found")):
                cpu_usage = get_cpu_usage()
                assert cpu_usage == 0.0

    def test_get_memory_usage_permission_error(self):
        """Test memory usage when /proc/meminfo is not accessible"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            with patch("builtins.open", side_effect=IOError("Permission denied")):
                memory_usage = get_memory_usage()
                assert memory_usage == 0.0

    def test_get_disk_io_os_error(self):
        """Test disk I/O when /proc/diskstats is not accessible"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            with patch("builtins.open", side_effect=OSError("OS Error")):
                disk_io = get_disk_io()
                assert disk_io == (0, 0)

    def test_get_network_io_unexpected_error(self):
        """Test network I/O error handling"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            with patch("builtins.open", side_effect=IOError("I/O error")):
                # The function should catch IOError and return (0, 0)
                network_io = get_network_io()
                assert network_io == (0, 0)

    def test_get_memory_usage_malformed_meminfo(self):
        """Test memory usage with malformed /proc/meminfo"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            with patch("builtins.open", mock_open(read_data="malformed data")):
                memory_usage = get_memory_usage()
                assert memory_usage == 0.0

    def test_get_disk_io_malformed_diskstats(self):
        """Test disk I/O with malformed /proc/diskstats"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            with patch("builtins.open", mock_open(read_data="malformed data")):
                disk_io = get_disk_io()
                assert disk_io == (0, 0)

    def test_get_network_io_malformed_net_dev(self):
        """Test network I/O with malformed /proc/net/dev"""
        with patch("monitoring.PSUTIL_AVAILABLE", False):
            with patch("builtins.open", mock_open(read_data="malformed data")):
                network_io = get_network_io()
                assert network_io == (0, 0)

    @patch("monitoring.get_cpu_usage")
    @patch("monitoring.get_memory_usage")
    @patch("monitoring.get_disk_io")
    @patch("monitoring.get_network_io")
    @patch("builtins.print")
    def test_main_function_json_output(
        self,
        mock_print,
        mock_network_io,
        mock_disk_io,
        mock_memory_usage,
        mock_cpu_usage,
    ):
        """Test main function JSON output format"""
        # Mock function returns
        mock_cpu_usage.return_value = 75.5
        mock_memory_usage.return_value = 60.2
        mock_disk_io.return_value = (1000, 2000)
        mock_network_io.return_value = (5000, 3000)

        # Call main function
        main()

        # Check that print was called
        mock_print.assert_called_once()

        # Get the printed output
        printed_output = mock_print.call_args[0][0]

        # Parse JSON
        data = json.loads(printed_output)

        # Verify the structure matches the actual implementation
        assert data["cpu_usage"] == 75.5
        assert data["memory_usage"] == 60.2
        assert data["disk_usage_read"] == 1000
        assert data["disk_usage_write"] == 2000
        assert data["network_usage_received"] == 5000
        assert data["network_usage_sent"] == 3000
        assert "psutil_available" in data

    def test_cpu_usage_with_psutil(self):
        """Test CPU usage with psutil available"""
        with patch("monitoring.PSUTIL_AVAILABLE", True):
            with patch("monitoring.psutil.cpu_percent", return_value=85.5):
                cpu_usage = get_cpu_usage()
                assert cpu_usage == 85.5

    def test_memory_usage_with_psutil(self):
        """Test memory usage with psutil available"""
        with patch("monitoring.PSUTIL_AVAILABLE", True):
            mock_vm = MagicMock()
            mock_vm.total = 8000000000  # 8GB
            mock_vm.available = 2000000000  # 2GB

            with patch("monitoring.psutil.virtual_memory", return_value=mock_vm):
                memory_usage = get_memory_usage()
                # Should be 2GB available out of 8GB total = 25%
                assert memory_usage == 25.0

    def test_disk_io_with_psutil(self):
        """Test disk I/O with psutil available"""
        with patch("monitoring.PSUTIL_AVAILABLE", True):
            mock_disk_io = MagicMock()
            mock_disk_io.read_count = 1000
            mock_disk_io.write_count = 2000

            with patch("monitoring.psutil.disk_io_counters", return_value=mock_disk_io):
                disk_io = get_disk_io()
                assert disk_io == (1000, 2000)

    def test_network_io_with_psutil(self):
        """Test network I/O with psutil available"""
        with patch("monitoring.PSUTIL_AVAILABLE", True):
            mock_net_io = MagicMock()
            mock_net_io.bytes_recv = 25000
            mock_net_io.bytes_sent = 50000

            with patch("monitoring.psutil.net_io_counters", return_value=mock_net_io):
                network_io = get_network_io()
                assert network_io == (25000, 50000)

    def test_psutil_exception_handling(self):
        """Test psutil exception handling"""
        with patch("monitoring.PSUTIL_AVAILABLE", True):
            with patch(
                "monitoring.psutil.cpu_percent", side_effect=Exception("psutil error")
            ):
                # The current implementation doesn't handle psutil exceptions
                # It will raise the exception instead of falling back
                with pytest.raises(Exception, match="psutil error"):
                    get_cpu_usage()
