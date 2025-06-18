#!/usr/bin/python3
import psutil,json
monitoring = {
    'cpu_usage': psutil.cpu_percent(),
    'memory_usage': psutil.virtual_memory().available * 100 / psutil.virtual_memory().total,
    'disk_usage_read': psutil.disk_io_counters(perdisk=False).read_count,
    'disk_usage_write': psutil.disk_io_counters(perdisk=False).write_count,
    'network_usage_received': psutil.net_io_counters(pernic=False).bytes_recv,
    'network_usage_sent': psutil.net_io_counters(pernic=False).bytes_sent
}

print(json.dumps(monitoring))




























