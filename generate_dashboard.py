import sqlite3

conn = sqlite3.connect("node_status.db")
cursor = conn.cursor()
cursor.execute("SELECT name, status, state, health_flag FROM container_status")
rows = cursor.fetchall()
conn.close()

html = "<!DOCTYPE html><html><head><title>Luther Node Dashboard</title><meta http-equiv='refresh' content='10'><style>body{font-family:monospace;background:#121212;color:#00ff00;padding:20px;}table{width:100%;border-collapse:collapse;margin-top:20px;}th,td{border:1px solid #333;padding:10px;text-align:left;}th{background:#1e1e1e;}.NORMAL{color:#00ff00;font-weight:bold;}.ERROR{color:#ff5555;font-weight:bold;}</style></head><body><h1>Luther Node Ecosystem</h1><table><tr><th>Container</th><th>Status</th><th>State</th><th>Health Flag</th></tr>"

for r in rows:
    css = "NORMAL" if "NORMAL" in r[3] else "ERROR"
    html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td class='css'>{r[3]}</td></tr>"

html += "</table></body></html>"

with open("index.html", "w") as f:
    f.write(html)

print("Dashboard generated successfully!")
