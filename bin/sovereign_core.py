#!/usr/bin/env python3
import os
import sqlite3
import argparse
import hashlib
import time
import socket
import psutil
from collections import deque

class HardwareTierManager:
    @staticmethod
    def detect_tier():
        try:
            total_ram_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = os.cpu_count() or 1
            if total_ram_gb <= 4 or cpu_count <= 2:
                return "EDGE_NODE", f"Lightweight IoT Profile ({total_ram_gb:.1f}GB RAM, {cpu_count} Cores)"
            else:
                return "CORE_HUB", f"High-Resource Federation Hub ({total_ram_gb:.1f}GB RAM, {cpu_count} Cores)"
        except Exception:
            return "EDGE_NODE", "Standard Edge Profile"

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

class SelfHealingNodeDoctor:
    def __init__(self, db_path):
        self.db_path = db_path

    def run_health_check_and_heal(self):
        """IoT Self-Healing loop: detects anomalies and triggers automated fixes."""
        report = {"status": "OPTIMAL", "actions_taken": [], "checks": []}
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            row = cur.fetchone()
            if row and row[0] == "ok":
                report["checks"].append({"name": "SQLite WAL Integrity", "passed": True})
            else:
                report["checks"].append({"name": "SQLite WAL Integrity", "passed": False})
                report["status"] = "DEGRADED"
                # Self-healing action: trigger WAL checkpoint and vacuum
                conn.execute("PRAGMA wal_checkpoint(RESTART);")
                report["actions_taken"].append("Executed emergency WAL checkpointing.")
            conn.close()
        except Exception as e:
            report["checks"].append({"name": "SQLite WAL Integrity", "passed": False, "detail": str(e)})
            report["status"] = "DEGRADED"
        return report

class SovereignNode:
    def __init__(self, is_regtest=True):
        self.is_regtest = is_regtest
        self.db_path = os.path.expanduser("~/node-stack/regtest_ledger.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.tier, self.tier_desc = HardwareTierManager.detect_tier()
        self.batcher = MicroStateBatcher(flush_threshold=3)
        self.doctor = SelfHealingNodeDoctor(self.db_path)
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
