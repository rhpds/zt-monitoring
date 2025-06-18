from fastapi import FastAPI
import sqlite3

app = FastAPI()

def to_sqlite_interval(shorthand: str) -> str:
    unit_map = {
        's': 'seconds',
        'm': 'minutes',
        'h': 'hours',
        'd': 'days',
        'w': 'weeks'
    }

    num = int(shorthand[:-1])
    unit = shorthand[-1]

    if unit not in unit_map:
        raise ValueError(f"Unsupported time unit: {unit}")

    return f"-{num} {unit_map[unit]}"

@app.get("/")
async def root():
    stats = {}
    con = sqlite3.connect("/tmp/metrics.db")
    cur = con.cursor()
    res = cur.execute("select host, avg(memory_usage) from memory_usage group by host")
    for host, value in res.fetchall():
        if host not in stats:
            stats[host] = {"memory": 0, "cpu": 0, "disk_read": 0, "disk_write": 0, "network_read": 0, "network_write": 0}
        stats[host]["memory"] = value
    res = cur.execute("select host, avg(cpu_usage) from cpu_usage group by host")
    for host, value in res.fetchall():
        stats[host]["cpu"] = value
    res = cur.execute("select host, avg(read), avg(write) from disk_usage group by host")
    for host, value_read, value_write in res.fetchall():
        print(host)
        stats[host]["disk_read"] = value_read
        stats[host]["disk_write"] = value_write
    res = cur.execute("select host, avg(received), avg(sent) from network_usage group by host")
    for host, value_rcv, value_sent in res.fetchall():
        stats[host]["network_read"] = value_rcv
        stats[host]["network_write"] = value_sent
    return stats

@app.get("/limit/{limit}")
async def filter(limit: str):
    stats = {}
    con = sqlite3.connect("/tmp/metrics.db")
    cur = con.cursor()
    res = cur.execute("select host from memory_usage group by host;")
    hosts = res.fetchall()
    limit_time = to_sqlite_interval(limit)
    for host_tuple in hosts:
        host = host_tuple[0]
        if host not in stats:
            stats[host] = {"memory": 0, "cpu": 0, "disk_read": 0, "disk_write": 0, "network_read": 0, "network_write": 0}
        res = cur.execute("select avg(memory_usage) from memory_usage where host='" + host + "' and timestamp >= datetime('now', 'localtime','" + limit_time + "')")

        stats[host]["memory"] = res.fetchone()[0]
        res = cur.execute("select avg(cpu_usage) from cpu_usage where host='" + host + "' and timestamp >= datetime('now', 'localtime','" + limit_time + "')")
        stats[host]["cpu"] = res.fetchone()[0]
        res = cur.execute("select avg(read), avg(write) from disk_usage where host='" + host + "' and timestamp >= datetime('now', 'localtime','" + limit_time + "')")
        disk_data = res.fetchone()
        stats[host]["disk_read"] = disk_data[0]
        stats[host]["disk_write"] = disk_data[1]
        res = cur.execute("select avg(received), avg(sent) from network_usage where host='" + host + "' and timestamp >= datetime('now', 'localtime','" + limit_time + "')")

        network_data = res.fetchone()
        stats[host]["network_read"] = network_data[0]
        stats[host]["network_write"] = network_data[1]
    return stats
