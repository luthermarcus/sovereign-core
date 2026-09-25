#!/usr/bin/env python3
import os, sqlite3, time

class ConnectionHealthAuditor:
    def __init__(self):
        self.db_path = os.path.expanduser("~/node-stack/sovereign_os_v2910.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("CREATE TABLE IF NOT EXISTS network_knowledge_base (ecosystem_id TEXT PRIMARY KEY, endpoint TEXT, protocol_version TEXT, health_score REAL, indexed_at REAL)")
        conn.execute("CREATE TABLE IF NOT EXISTS connection_audit_status (ecosystem_id TEXT PRIMARY KEY, endpoint TEXT, connection_status TEXT, last_checked REAL)")
        conn.commit()
        conn.close()

    def run_audit_cycle(self):
        print("[*] Launching Connection Health Auditor & Crawler...")
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        
        blocked = [row[0] for row in conn.execute("SELECT endpoint FROM connection_firewall_log WHERE action='BLOCKED'").fetchall()]
        knowledge_entries = conn.execute("SELECT ecosystem_id, endpoint FROM network_knowledge_base").fetchall()

        available_unconnected = 0
        for eco_id, endpoint in knowledge_entries:
            if endpoint in blocked:
                status = "FIREWALLED"
            else:
                # Simulate health check / availability test
                status = "AVAILABLE_UNCONNECTED" if "10.0.0." in endpoint or "192.168." in endpoint else "CONNECTED"
                if status == "AVAILABLE_UNCONNECTED":
                    available_unconnected += 1

            conn.execute("INSERT OR REPLACE INTO connection_audit_status VALUES (?, ?, ?, ?)", (eco_id, endpoint, status, now))

        conn.commit()
        conn.close()
        print(f"[✓] Audit complete. Found {available_unconnected} backend endpoints available but unconnected.")

if __name__ == "__main__":
    auditor = ConnectionHealthAuditor()
    auditor.run_audit_cycle()
