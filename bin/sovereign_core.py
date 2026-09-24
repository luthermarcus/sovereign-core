#!/usr/bin/env python3
import os
import sqlite3
import argparse
import hashlib
import time
import socket

class DePINGovernor:
    def __init__(self, difficulty=2):
        self.difficulty = difficulty

    def apply_thermal_limits(self):
        try: os.nice(15)
        except (AttributeError, PermissionError): pass

    def solve_proof(self, node_address):
        nonce = 0
        prefix = '0' * self.difficulty
        start_time = time.time()
        while True:
            # High-resolution time seed guarantees unique hashes across rapid test runs
            candidate = f"{node_address}{nonce}{time.time()}".encode()
            hash_result = hashlib.sha256(candidate).hexdigest()
            if hash_result.startswith(prefix):
                return hash_result, nonce, time.time() - start_time
            nonce += 1

class HardwareWalletBridge:
    @staticmethod
    def generate_psbt(recipient, amount):
        return {
            "type": "PSBT_RAW_HEX",
            "payload": f"70736274ff010079020000000100000000000000000000000000000000000000000000000000000000000000000000000000ffffffff01{int(amount*100000000):016x}160014{hashlib.sha256(recipient.encode()).hexdigest()[:40]}00000000",
            "recipient": recipient,
            "amount_fox": amount,
            "status": "Awaiting Air-Gapped Signature"
        }

class NodeDoctor:
    def __init__(self, db_path, lockdown=False):
        self.db_path = db_path
        self.lockdown = lockdown

    def run_diagnostics(self):
        results = {"status": "OPTIMAL", "checks": []}
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            row = cur.fetchone()
            if row and row[0] == "ok":
                results["checks"].append({"name": "SQLite WAL Integrity", "passed": True, "detail": "PRAGMA OK"})
            else:
                results["checks"].append({"name": "SQLite WAL Integrity", "passed": False, "detail": "Corrupted"})
                results["status"] = "DEGRADED"
            conn.close()
        except Exception as e:
            results["checks"].append({"name": "SQLite WAL Integrity", "passed": False, "detail": str(e)})
            results["status"] = "DEGRADED"

        sandbox_dir = os.path.expanduser("~/sovereign-ecosystem/sandbox_apps")
        os.makedirs(sandbox_dir, exist_ok=True)
        if os.access(sandbox_dir, os.W_OK):
            results["checks"].append({"name": "WASI Sandbox", "passed": True, "detail": "Read/Write OK"})
        else:
            results["checks"].append({"name": "WASI Sandbox", "passed": False, "detail": "Read-only filesystem"})
            results["status"] = "DEGRADED"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            in_use = (s.connect_ex(('127.0.0.1', 8545)) == 0)
            results["checks"].append({"name": "API Port (8545)", "passed": True, "detail": "Active" if in_use else "Available"})

        return results

class SovereignNode:
    def __init__(self, is_regtest=True):
        self.is_regtest = is_regtest
        self.db_path = os.path.expanduser("~/node-stack/regtest_ledger.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.governor = DePINGovernor(difficulty=2)
        self.governor.apply_thermal_limits()
        self.doctor = NodeDoctor(self.db_path)
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
            cur.execute("CREATE TABLE IF NOT EXISTS feature_bounties (bounty_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, target REAL, funded REAL DEFAULT 0.0)")
            
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('genesis_faucet', 'FOX', 100000.0)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('genesis_treasury', 'FOX', 0.0)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('depin_pool', 'FOX', 0.0)")
            conn.commit()

    def prune_ledger(self, keep_days=7):
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM depin_proofs WHERE timestamp <= datetime('now', '-{keep_days} days')")
            deleted = cur.rowcount
            conn.commit()
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.execute("VACUUM;")
        conn.close()
        return {"status": "pruned", "cleared_records": deleted}

    def process_5_5_90_split(self, sender_addr, creator_addr, amount):
        if amount <= 0: raise ValueError("Amount must exceed zero.")
        creator_fee = amount * 0.05
        treasury_fee = amount * 0.05
        depin_reward = amount * 0.90

        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM accounts WHERE address = ?", (sender_addr,))
            row = cur.fetchone()
            if not row or row[0] < amount: raise ValueError("Insufficient funds")

            cur.execute("UPDATE accounts SET balance = balance - ? WHERE address = ?", (amount, sender_addr))
            cur.execute("INSERT INTO accounts (address, token, balance) VALUES (?, 'FOX', ?) ON CONFLICT(address) DO UPDATE SET balance = balance + ?", (creator_addr, creator_fee, creator_fee))
            cur.execute("UPDATE accounts SET balance = balance + ? WHERE address = 'genesis_treasury'", (treasury_fee,))
            cur.execute("UPDATE accounts SET balance = balance + ? WHERE address = 'depin_pool'", (depin_reward,))
            conn.commit()
        return {"creator_fee": creator_fee, "treasury_fee": treasury_fee, "depin_reward": depin_reward}

    def record_compute_proof(self, node_address):
        h, nonce, dur = self.governor.solve_proof(node_address)
        with self.get_conn() as conn:
            conn.execute("INSERT INTO depin_proofs (hash, nonce, difficulty) VALUES (?, ?, ?)", (h, nonce, self.governor.difficulty))
            conn.execute("UPDATE accounts SET balance = balance + 10.0 WHERE address = 'depin_pool'")
            conn.execute("INSERT INTO accounts (address, token, balance) VALUES (?, 'FOX', 10.0) ON CONFLICT(address) DO UPDATE SET balance = balance + 10.0", (node_address,))
            conn.commit()
        return {"hash": h, "nonce": nonce, "duration_sec": round(dur, 3), "reward_fox": 10.0}
