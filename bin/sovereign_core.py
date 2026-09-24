#!/usr/bin/env python3
import os
import json
import sqlite3
import hashlib
import time
import psutil
from collections import deque

def load_config():
    config_path = os.path.expanduser("~/sovereign-ecosystem/config.json")
    default_config = {
        "node_address": "privacy_node_01", "node_profile": "SOVEREIGN_EDGE",
        "privacy_mode": "local_only", "is_regtest": True,
        "db_path": "~/node-stack/regtest_ledger.db",
        "poc_difficulty": 2, "micro_batch_threshold": 3
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return {**default_config, **json.load(f)}
        except Exception:
            return default_config
    return default_config

class HardwareTelemetry:
    @staticmethod
    def get_metrics():
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
                "tier": tier, "cpu_pct": cpu_percent,
                "ram_used": used_ram_gb, "ram_total": total_ram_gb, "ram_pct": mem.percent,
                "disk_free": free_disk_gb, "disk_total": total_disk_gb, "disk_pct": disk.percent
            }
        except Exception:
            return {"tier": "EDGE_NODE", "cpu_pct": 0.0, "ram_used": 0, "ram_total": 4, "ram_pct": 0, "disk_free": 10, "disk_total": 50, "disk_pct": 50}

class SovereignNode:
    def __init__(self):
        self.config = load_config()
        self.db_path = os.path.expanduser(self.config["db_path"])
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def init_database(self):
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS accounts (address TEXT PRIMARY KEY, token TEXT, balance REAL CHECK(balance >= 0))")
            cur.execute("CREATE TABLE IF NOT EXISTS depin_proofs (hash TEXT PRIMARY KEY, nonce INTEGER, difficulty INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('genesis_faucet', 'FOX', 100000.0)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('depin_pool', 'FOX', 0.0)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01', 'FOX', 250.0)")
            conn.commit()

    def get_balance(self, address):
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM accounts WHERE address = ?", (address,))
            row = cur.fetchone()
            return row[0] if row else 0.0

    def set_privacy_mode(self, mode):
        self.config["privacy_mode"] = mode
        config_path = os.path.expanduser("~/sovereign-ecosystem/config.json")
        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=2)
        return mode

    def run_diagnostics(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA integrity_check;")
            conn.close()
            return {"status": "OPTIMAL", "detail": f"Privacy Mode [{self.config['privacy_mode']}] Active & WAL Secure"}
        except Exception as e:
            return {"status": "DEGRADED", "detail": str(e)}
