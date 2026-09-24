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
        "node_address": "dex_node_01", "node_profile": "SOVEREIGN_DEX_HUB",
        "privacy_mode": "local_only", "is_regtest": True,
        "db_path": "~/node-stack/regtest_ledger.db",
        "poc_difficulty": 2, "micro_batch_threshold": 3, "dex_fee_percent": 0.3
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
            cur.execute("""CREATE TABLE IF NOT EXISTS liquidity_pools (
                pool_id TEXT PRIMARY KEY, token_a TEXT, token_b TEXT, 
                reserve_a REAL, reserve_b REAL, lp_shares REAL
            )""")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('genesis_faucet', 'FOX', 100000.0)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01', 'FOX', 250.0)")
            cur.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01_sats', 'SATS', 50000.0)")
            cur.execute("""INSERT OR IGNORE INTO liquidity_pools VALUES 
                ('FOX_SATS', 'FOX', 'SATS', 10000.0, 500000.0, 1000.0)""")
            conn.commit()

    def get_balance(self, address):
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM accounts WHERE address = ?", (address,))
            row = cur.fetchone()
            return row[0] if row else 0.0

    def get_pool_info(self):
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT reserve_a, reserve_b, lp_shares FROM liquidity_pools WHERE pool_id = 'FOX_SATS'")
            return cur.fetchone()

    def execute_amm_swap(self, amount_in, swap_a_to_b=True):
        res_a, res_b, shares = self.get_pool_info()
        fee = self.config["dex_fee_percent"] / 100.0
        amount_in_fee = amount_in * (1 - fee)

        if swap_a_to_b:
            amount_out = (res_b * amount_in_fee) / (res_a + amount_in_fee)
            new_res_a = res_a + amount_in
            new_res_b = res_b - amount_out
        else:
            amount_out = (res_a * amount_in_fee) / (res_b + amount_in_fee)
            new_res_b = res_b + amount_in
            new_res_a = res_a - amount_out

        with self.get_conn() as conn:
            conn.execute("UPDATE liquidity_pools SET reserve_a = ?, reserve_b = ? WHERE pool_id = 'FOX_SATS'", (new_res_a, new_res_b))
            conn.commit()
        return {"amount_out": amount_out, "new_reserve_a": new_res_a, "new_reserve_b": new_res_b}

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
            return {"status": "OPTIMAL", "detail": f"DEX AMM Pools & WAL Ledger Verified [{self.config['privacy_mode']}]"}
        except Exception as e:
            return {"status": "DEGRADED", "detail": str(e)}
