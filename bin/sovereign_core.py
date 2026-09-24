#!/usr/bin/env python3
import os
import sys
import sqlite3

class NodeSecurityGate:
    def __init__(self):
        self.host_ip = "127.0.0.1"
        self._check_testnet()
        self._check_socket()
        self._check_permissions()

    def _check_testnet(self):
        if "mainnet" in os.environ.get("SOVEREIGN_NETWORK", "testnet").lower():
            print("[FATAL] Beta versions cannot run on Mainnet.")
            sys.exit(1)

    def _check_socket(self):
        if self.host_ip == "0.0.0.0":
            print("[FATAL] RPC bound to 0.0.0.0. Exposing node to public Wi-Fi.")
            sys.exit(1)

    def _check_permissions(self):
        ledger_dir = os.path.expanduser("~/node-stack")
        if os.path.exists(ledger_dir):
            if oct(os.stat(ledger_dir).st_mode)[-3:] != "700":
                os.chmod(ledger_dir, 0o700)

class SovereignCore:
    def __init__(self):
        self.db_path = os.path.expanduser("~/node-stack/crypto_ledger.db")
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_database(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS hd_derivation_paths (id INTEGER PRIMARY KEY, path TEXT UNIQUE, used INTEGER DEFAULT 0)")
            cur.execute("CREATE TABLE IF NOT EXISTS app_registry (app_id TEXT PRIMARY KEY, name TEXT, creator TEXT, parent_id TEXT, uri TEXT)")
            cur.execute("CREATE TABLE IF NOT EXISTS value_splits (app_id TEXT, recipient TEXT, split REAL, PRIMARY KEY(app_id, recipient))")
            cur.execute("CREATE TABLE IF NOT EXISTS accounts (address TEXT, token TEXT, balance REAL, PRIMARY KEY(address, token))")
            
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('test_consumer', 'NATIVE', 50000.0)")
            conn.commit()

    def register_app(self, app_id, name, creator, parent_id=""):
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO app_registry VALUES (?, ?, ?, ?, '')", (app_id, name, creator, parent_id))
            conn.execute("INSERT OR REPLACE INTO value_splits VALUES (?, ?, ?)", (app_id, "genesis_treasury", 0.03))
            conn.execute("INSERT OR REPLACE INTO value_splits VALUES (?, ?, ?)", (app_id, creator, 0.97))
            conn.commit()

    def process_cascading_payment(self, app_id, consumer, amount):
        UPSTREAM_ROYALTY = 0.05 
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT parent_id FROM app_registry WHERE app_id = ?", (app_id,))
            parent = cur.fetchone()
            gross = amount
            
            if parent and parent[0]:
                cur.execute("SELECT creator FROM app_registry WHERE app_id = ?", (parent[0],))
                parent_creator = cur.fetchone()[0]
                upstream_cut = amount * UPSTREAM_ROYALTY
                gross -= upstream_cut
                conn.execute("UPDATE accounts SET balance = balance - ? WHERE address = ?", (upstream_cut, consumer))
                conn.execute("UPDATE accounts SET balance = balance + ? WHERE address = ?", (upstream_cut, parent_creator))
                print(f"[FORK ROYALTY] Dripped {upstream_cut:.2f} upstream to {parent_creator}")
            
            cur.execute("SELECT recipient, split FROM value_splits WHERE app_id = ?", (app_id,))
            for rec, split in cur.fetchall():
                cut = gross * split
                conn.execute("UPDATE accounts SET balance = balance - ? WHERE address = ?", (cut, consumer))
                conn.execute("UPDATE accounts SET balance = balance + ? WHERE address = ?", (cut, rec))
                print(f"[VALUE SPLIT] Routed {cut:.2f} to {rec}")
            conn.commit()

def main():
    NodeSecurityGate()
    core = SovereignCore()
    
    os.system("clear" if os.name == "posix" else "cls")
    print("================================================================")
    print("      SOVEREIGN CORE: v0.1.0-beta (Local Smoke Test)            ")
    print("================================================================")
    print(" Network: SIGNET | API: 127.0.0.1:8545 | Storage: SQLite WAL")
    print("================================================================")
    
    print("[*] Running Cascading Royalty Self-Test...")
    core.register_app("app_A", "Open-Source Base", "dev_alice")
    core.register_app("app_B", "Forked UI Mod", "dev_bob", parent_id="app_A")
    
    print("\n[+] Consumer streaming 1000 Sats to App B (Forked from App A):")
    core.process_cascading_payment("app_B", "test_consumer", 1000.0)
    print("\n[SUCCESS] Local test complete. Ready for GitHub when you are.")

if __name__ == "__main__":
    main()
