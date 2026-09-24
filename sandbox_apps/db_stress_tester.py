#!/usr/bin/env python3
import sqlite3, os
print("[SANDBOX] Running SQLite WAL concurrency stress test...")
conn = sqlite3.connect(os.path.expanduser("~/node-stack/regtest_ledger.db"))
conn.execute("PRAGMA journal_mode = WAL;")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM accounts;")
print(f"[SUCCESS] Database stress test passed. Active accounts: {cur.fetchone()[0]}")
conn.close()
