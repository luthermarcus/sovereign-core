import sqlite3
import subprocess

conn = sqlite3.connect("node_status.db")
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS container_status (name TEXT PRIMARY KEY, status TEXT, state TEXT, health_flag TEXT)')

cmd = ["docker", "ps", "-a", "--format", "{{.Names}}|{{.Status}}|{{.State}}"]
result = subprocess.run(cmd, capture_output=True, text=True)

for line in result.stdout.strip().split("\n"):
    if line:
        parts = line.split("|")
        if len(parts) == 3:
            name, status, state = parts
            flag = "NORMAL" if state == "running" else "ERROR - RESTARTING"
            cursor.execute('INSERT OR REPLACE INTO container_status VALUES (?, ?, ?, ?)', (name, status, state, flag))

conn.commit()
conn.close()
print("Monitor executed successfully!")
