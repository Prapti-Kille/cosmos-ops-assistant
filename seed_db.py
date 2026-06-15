import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("incidents.db")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY,
    title TEXT,
    db_type TEXT,
    severity TEXT,
    root_cause TEXT,
    mttr_minutes INTEGER,
    created_at TEXT,
    resolved_at TEXT,
    status TEXT
)''')

db_types = ["Azure SQL DB", "Cosmos DB", "PostgreSQL (OSS)", "Azure SQL DB", "Cosmos DB"]
severities = ["P0", "P1", "P1", "P2", "P2", "P2"]
root_causes = [
    "Query timeout due to missing index",
    "Replication lag exceeding threshold",
    "Storage capacity exhausted",
    "Connection pool saturation",
    "CPU throttling under peak load",
    "Deadlock in transaction processing",
    "Network partition between replicas",
    "Backup job consuming I/O bandwidth",
    "Schema migration blocking reads",
    "Authentication service latency spike"
]

titles = [
    "High latency on read queries",
    "Write throughput degraded",
    "Replication behind by >5 min",
    "Connection errors spiking",
    "Storage utilization critical",
    "Query execution timeout",
    "Deadlock detected in workload",
    "Backup job causing I/O contention",
    "Schema migration blocking reads",
    "Auth failures on DB connections"
]

incidents = []
base_date = datetime.now() - timedelta(days=90)

for i in range(30):
    created = base_date + timedelta(days=random.randint(0, 89), hours=random.randint(0, 23))
    sev = random.choice(severities)
    mttr = random.randint(15, 45) if sev == "P0" else random.randint(30, 180) if sev == "P1" else random.randint(60, 480)
    resolved = created + timedelta(minutes=mttr)
    incidents.append((
        random.choice(titles),
        random.choice(db_types),
        sev,
        random.choice(root_causes),
        mttr,
        created.strftime("%Y-%m-%d %H:%M"),
        resolved.strftime("%Y-%m-%d %H:%M"),
        "Resolved"
    ))

c.executemany("INSERT INTO incidents (title, db_type, severity, root_cause, mttr_minutes, created_at, resolved_at, status) VALUES (?,?,?,?,?,?,?,?)", incidents)
conn.commit()
conn.close()
print("DB seeded with 30 incidents.")
