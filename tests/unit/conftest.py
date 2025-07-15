"""
Unit test fixtures
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import Any

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_proc_stat() -> str:
    """Mock /proc/stat content for CPU testing"""
    return "cpu  123456 0 654321 999999 0 0 0 0 0 0\n"


@pytest.fixture
def mock_proc_meminfo() -> str:
    """Mock /proc/meminfo content for memory testing"""
    return (
        "MemTotal:        8000000 kB\n"
        "MemFree:         2000000 kB\n"
        "MemAvailable:    4000000 kB\n"
        "Buffers:          500000 kB\n"
        "Cached:          1500000 kB\n"
    )


@pytest.fixture
def mock_proc_diskstats() -> str:
    """Mock /proc/diskstats content for disk I/O testing"""
    return (
        "   8       0 sda 1000 0 0 0 2000 0 0 0 0 0 0 0 0 0 0 0 0\n"  # noqa: E501
        "   8       1 sda1 100 0 0 0 200 0 0 0 0 0 0 0 0 0 0 0 0\n"  # noqa: E501
    )


@pytest.fixture
def mock_proc_net_dev() -> str:
    """Mock /proc/net/dev content for network I/O testing"""
    return (
        "Inter-|   Receive                                                |  Transmit\n"  # noqa: E501
        " face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed\n"  # noqa: E501
        "    lo:    1000     100    0    0    0     0          0         0     1000     100    0    0    0     0       0          0\n"  # noqa: E501
        "  eth0:   50000     500    0    0    0     0          0         0    25000     250    0    0    0     0       0          0\n"  # noqa: E501
    )


@pytest.fixture
def mock_psutil_unavailable() -> Any:
    """Mock psutil as unavailable for testing fallback mechanisms"""
    with patch("monitoring.PSUTIL_AVAILABLE", False):
        yield


@pytest.fixture
def mock_file_operations() -> Any:
    """Mock file operations for testing"""
    with patch("builtins.open", mock_open()) as mock_file:
        yield mock_file
