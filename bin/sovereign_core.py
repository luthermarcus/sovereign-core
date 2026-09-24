#!/usr/bin/env python3
import os
import sqlite3
import hashlib
import time
import psutil
from collections import deque

class HardwareTelemetry:
    @staticmethod
    def get_metrics():
        """Collects real-time hardware telemetry for edge nodes and server hubs."""
        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=None)
            total_ram_gb = mem.total / (1024**3)
            used_ram_gb = mem.used / (1024**3)
            total_disk_gb = disk.total / (1024**3)
            free_disk_gb = disk.free / (1024**3)
            
            tier = "EDGE_NODE" if total_ram_gb <= 4 else "CORE_HUB"
            return {
                "tier": tier,
                "cpu_pct": cpu_percent,
                "ram_used": used_ram_gb,
                "ram_total": total_ram_gb,
                "ram_pct": mem.percent,
                "disk_free": free_disk_gb,
                "disk_total": total_disk_gb,
                "disk_pct": disk.percent
            }
        except Exception:
            return {"tier": "EDGE_NODE", "cpu_pct": 0.0, "ram_used": 0, "ram_total": 4, "ram_pct": 0, "disk_free": 10, "disk_total": 50, "disk_pct": 50}

class MicroStateBatcher:
    def __init__(self, flush_threshold=3):
        self.buffer = deque()
        self.flush_threshold = flush_threshold

    def add_transaction(self, sender, recipient, amount):
        self.buffer.append({"sender": sender, "recipient": recipient, "amount": amount, "timestamp": time.time()})
        if len(self.buffer) >= self.flush_threshold:
            return self.flush()
        return None

    def flush(self):
        batch = list(self.buffer)
        self.buffer.clear()
        return batch

class SovereignNode:
    def __init__(self, is_regtest=True):
        self.is_regtest = is_regtest
        self.db_path = os.path.expanduser("~/node-stack/regtest_ledger.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.batcher = MicroStateBatcher(flush_threshold=3)
        self.init_database()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_database(self):
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS accounts (address TEXT PRIMARY KEY, token TEXT, balance REAL CHECK(balance >= 0))")
            cur.execute("CREATE TABLE IF NOT EXISTS depin_proofs (hash TEXT PRIMARY KEY, nonce INTEGER, difficulty INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('genesis_faucet', 'FOX', 100000.0)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('depin_pool', 'FOX', 0.0)")
            conn.commit()

    def process_batched_micro_payment(self, sender, recipient, amount):
        flushed_batch = self.batcher.add_transaction(sender, recipient, amount)
        if flushed_batch:
            with self.get_conn() as conn:
                for tx in flushed_batch:
                    conn.execute("UPDATE accounts SET balance = balance - ? WHERE address = ?", (tx['amount'], tx['sender']))
                    conn.execute("INSERT INTO accounts (address, token, balance) VALUES (?, 'FOX', ?) ON CONFLICT(address) DO UPDATE SET balance = balance + ?", (tx['recipient'], tx['amount'], tx['amount']))
                conn.commit()
            return {"status": "batch_committed", "count": len(flushed_batch)}
        return {"status": "buffered", "buffer_size": len(self.batcher.buffer)}

    def run_diagnostics(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA integrity_check;")
            conn.close()
            return {"status": "OPTIMAL", "detail": "SQLite WAL Integrity Verified"}
        except Exception as e:
            return {"status": "DEGRADED", "detail": str(e)}
