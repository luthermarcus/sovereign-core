#!/usr/bin/env python3
import os, json, sqlite3, hashlib, time, socket, threading, base64, glob, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
sys.path.append(os.path.dirname(__file__))
from sovereign_key_vault import SelfCustodyKeyVault

def load_manifest():
    path = os.path.expanduser("~/sovereign-ecosystem/fork_manifest.json")
    try:
        with open(path, 'r') as f: return json.load(f)
    except: return {}

class SovereignNode:
    def __init__(self):
        self.config = load_manifest()
        self.db_path = os.path.expanduser(self.config.get("db_path", "~/node-stack/sovereign_os_v2912.db"))
        self.backup_dir = os.path.expanduser("~/sovereign-ecosystem/backups")
        self.media_dir = os.path.expanduser("~/sovereign-ecosystem/media_cache")
        self.mail_dir = os.path.expanduser("~/sovereign-ecosystem/mail")
        self.modules_dir = os.path.expanduser("~/sovereign-ecosystem/modules")
        self.vault_path = os.path.expanduser("~/sovereign-ecosystem/vault/master.key")
        self.auth_cookie_path = os.path.expanduser("~/sovereign-ecosystem/vault/rpc_auth.cookie")
        self.bound_rest_port = None
        self.current_version = "v2.9.12-beta"

        self.key_vault = SelfCustodyKeyVault()
        self._init_security_vaults()
        self.run_adaptive_diagnostics_and_pruning()
        self.start_resilient_rest_api()
        self.start_autonomous_watchdog()

    def _init_security_vaults(self):
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
        if not os.path.exists(self.vault_path):
            with open(self.vault_path, 'w') as f: f.write(os.urandom(32).hex())
        with open(self.vault_path, 'r') as f: self.master_key = f.read().strip()
        
        self.api_token = os.urandom(32).hex()
        with open(self.auth_cookie_path, 'w') as f: f.write(f"sov_rpc:{self.api_token}")

    def get_conn(self, target_path=None):
        path = target_path or self.db_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA mmap_size = 268435456;")
        conn.execute("PRAGMA temp_store = MEMORY;")
        return conn

    def run_adaptive_diagnostics_and_pruning(self):
        os.makedirs(os.path.expanduser("~/node-stack"), exist_ok=True)
        os.makedirs(self.media_dir, exist_ok=True)
        os.makedirs(self.mail_dir, exist_ok=True)
        os.makedirs(self.modules_dir, exist_ok=True)
        
        channel = self.config.get("release_channel", "BETA")
        ff = self.config.get("feature_flags", {})
        
        with self.get_conn() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS accounts (address TEXT PRIMARY KEY, cipher_payload TEXT, balance REAL CHECK(balance >= 0))")
            conn.execute("CREATE TABLE IF NOT EXISTS utxo_ledger (utxo_id TEXT PRIMARY KEY, address TEXT, amount REAL, is_spent INTEGER, txid TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS liquidity_pools (pool_id TEXT PRIMARY KEY, reserve_a REAL, reserve_b REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS system_flags (flag_key TEXT PRIMARY KEY, level TEXT, status TEXT, message TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS network_peers (peer_id TEXT PRIMARY KEY, ip_address TEXT, version TEXT, status TEXT, ping_ms REAL, banscore INTEGER, last_seen REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS transaction_ledger (tx_id TEXT PRIMARY KEY, type TEXT, amount REAL, fee REAL, counterparty TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS cross_chain_bridge (swap_id TEXT PRIMARY KEY, amount REAL, preimage_hash TEXT, status TEXT, expires_at REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS trusted_contacts (address TEXT PRIMARY KEY, alias TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS connection_firewall_log (firewall_id TEXT PRIMARY KEY, endpoint TEXT, action TEXT, reason TEXT, timestamp REAL)")

            if channel in ["BETA", "SIMULATION", "DEV"]:
                if ff.get("sandbox_bypass_override"):
                    conn.execute("INSERT OR REPLACE INTO system_flags VALUES ('SANDBOX_BYPASS', 'WARN', 'ACTIVE', 'Encrypted Sandbox Override Engaged', ?)", (time.time(),))
                else:
                    conn.execute("DELETE FROM system_flags WHERE flag_key='SANDBOX_BYPASS'")
            else:
                conn.execute("DROP TABLE IF EXISTS connection_firewall_log;")
                conn.execute("DELETE FROM system_flags WHERE flag_key='SANDBOX_BYPASS'")

            vault_info = self.key_vault.get_user_vault_details()
            user_addr = vault_info.get("owner_sovereign_address", "sov1_default")

            conn.execute("INSERT OR IGNORE INTO accounts VALUES (?, ?, 250.0)", (user_addr, base64.b64encode(b"user").decode(),))
            conn.execute("INSERT OR IGNORE INTO accounts VALUES (?, ?, 50000.0)", (f"{user_addr}_sats", base64.b64encode(b"sats").decode(),))
            conn.execute("INSERT OR IGNORE INTO utxo_ledger VALUES ('utxo_genesis_01', ?, 150.0, 0, 'txid_gen_1')", (user_addr,))
            conn.execute("INSERT OR IGNORE INTO utxo_ledger VALUES ('utxo_genesis_02', ?, 100.0, 0, 'txid_gen_2')", (user_addr,))
            conn.execute("INSERT OR IGNORE INTO liquidity_pools VALUES ('MAIN_POOL', 10000.0, 500000.0)")
            conn.execute("INSERT OR IGNORE INTO trusted_contacts VALUES ('0xVerifiedColdStorage', 'Primary Vault')")
            
            now = time.time()
            conn.execute("INSERT OR IGNORE INTO network_peers VALUES ('peer_node_alpha', '10.0.0.1', 'v2.9.12-beta', 'ACTIVE', 12.5, 0, ?)", (now,))
            conn.execute("INSERT OR IGNORE INTO connection_firewall_log VALUES ('fw_sample_01', '198.51.100.42:9050', 'BLOCKED', 'Untrusted external scraper IP blocked by Sovereign Firewall.', ?)", (now - 300,))
            conn.commit()

    def get_utxo_list(self):
        vault_info = self.key_vault.get_user_vault_details()
        user_addr = vault_info.get("owner_sovereign_address", "sov1_default")
        with self.get_conn() as conn:
            return conn.execute("SELECT utxo_id, amount, txid FROM utxo_ledger WHERE address=? AND is_spent=0", (user_addr,)).fetchall()

    def get_local_storage_usage(self):
        total_bytes = 0
        stack_dir = os.path.expanduser("~/node-stack")
        if os.path.isdir(stack_dir):
            for root, dirs, files in os.walk(stack_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp): total_bytes += os.path.getsize(fp)
        return total_bytes / (1024 * 1024)

    def toggle_feature_flag(self, flag_key):
        path = os.path.expanduser("~/sovereign-ecosystem/fork_manifest.json")
        try:
            with open(path, 'r') as f: manifest = json.load(f)
            flags = manifest.get("feature_flags", {})
            if flag_key in flags:
                flags[flag_key] = not flags[flag_key]
                manifest["feature_flags"] = flags
                with open(path, 'w') as f: json.dump(manifest, f, indent=2)
                return {"status": "SUCCESS", "flag": flag_key, "new_state": flags[flag_key]}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        return {"status": "NOT_FOUND"}

    def execute_custom_sql(self, query):
        with self.get_conn() as conn:
            try:
                cursor = conn.execute(query)
                if query.strip().upper().startswith("SELECT"):
                    return {"status": "SUCCESS", "rows": cursor.fetchall()}
                else:
                    conn.commit()
                    return {"status": "SUCCESS", "message": "Query executed successfully."}
            except Exception as e:
                return {"status": "ERROR", "message": str(e)}

    def create_live_backup(self):
        os.makedirs(self.backup_dir, exist_ok=True)
        backup_file = os.path.join(self.backup_dir, f"sovereign_backup_{int(time.time())}.db")
        try:
            with self.get_conn() as conn:
                conn.execute(f"VACUUM INTO '{backup_file}'")
            return {"status": "SUCCESS", "file": backup_file}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def send_transaction_with_fee(self, recipient, amount, fee_rate):
        vault_info = self.key_vault.get_user_vault_details()
        user_addr = vault_info.get("owner_sovereign_address", "sov1_default")
        tx_id = f"tx_{int(time.time())}_{os.urandom(2).hex()}"
        now = time.time()
        total_cost = amount + fee_rate

        with self.get_conn() as conn:
            bal = conn.execute("SELECT balance FROM accounts WHERE address=?", (user_addr,)).fetchone()[0]
            if bal < total_cost: return {"status": "ERROR", "message": f"Insufficient funds. Required: {total_cost} FOX"}
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE address=?", (total_cost, user_addr))
            conn.execute("INSERT OR IGNORE INTO accounts VALUES (?, ?, 0.0)", (recipient, base64.b64encode(b"recipient").decode()))
            conn.execute("UPDATE accounts SET balance = balance + ? WHERE address = ?", (amount, recipient))
            conn.execute("INSERT INTO transaction_ledger VALUES (?, 'DEBIT', ?, ?, ?, ?)", (tx_id, amount, fee_rate, recipient, now))
            conn.commit()
        return {"status": "SUCCESS", "tx_id": tx_id, "amount": amount, "fee": fee_rate, "recipient": recipient}

    def start_resilient_rest_api(self):
        outer = self
        class SecureAPIHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.headers.get('Authorization') != f"sov_rpc:{outer.api_token}":
                    self.send_response(401); self.end_headers(); return
                self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(outer.query_full_status()).encode())
            def log_message(self, format, *args): pass
        class ReusableServer(HTTPServer): allow_reuse_address = True
        for p in [8080, 8088]:
            try:
                srv = ReusableServer(('127.0.0.1', p), SecureAPIHandler)
                self.bound_rest_port = p
                threading.Thread(target=srv.serve_forever, daemon=True).start()
                break
            except Exception: continue

    def start_autonomous_watchdog(self):
        threading.Thread(target=self._watchdog_loop, daemon=True).start()

    def _watchdog_loop(self):
        while True:
            try:
                usage = self.get_local_storage_usage()
                cap = self.config.get("storage_allocation_mb", 500)
                if usage > (cap * 0.9):
                    self.set_system_flag("STORAGE_CAP", "WARN", "ACTIVE", f"Storage near limit: {usage:.1f}MB")
                else:
                    self.set_system_flag("STORAGE_CAP", "INFO", "CLEARED", f"Storage Healthy ({usage:.1f}MB)")
            except: pass
            time.sleep(10)

    def set_system_flag(self, flag_key, level, status, message):
        with self.get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO system_flags VALUES (?, ?, ?, ?, ?)", (flag_key, level, status, message, time.time()))
            conn.commit()

    def query_system_flags(self):
        with self.get_conn() as conn:
            rows = conn.execute("SELECT flag_key, level, status, message FROM system_flags ORDER BY timestamp DESC").fetchall()
            return [{"key": r[0], "level": r[1], "status": r[2], "message": r[3]} for r in rows]
    
    def query_full_status(self):
        vault_info = self.key_vault.get_user_vault_details()
        user_addr = vault_info.get("owner_sovereign_address", "sov1_default")
        
        with self.get_conn() as conn:
            ra, rb = conn.execute("SELECT reserve_a, reserve_b FROM liquidity_pools WHERE pool_id = 'MAIN_POOL'").fetchone()
            fox_row = conn.execute("SELECT balance FROM accounts WHERE address=?", (user_addr,)).fetchone()
            sats_row = conn.execute("SELECT balance FROM accounts WHERE address=?", (f"{user_addr}_sats",)).fetchone()
            
            fox = fox_row[0] if fox_row else 250.0
            sats = sats_row[0] if sats_row else 50000.0
            
            utxo_count = conn.execute("SELECT COUNT(*) FROM utxo_ledger WHERE address=? AND is_spent=0", (user_addr,)).fetchone()[0]
            blocked_conn = conn.execute("SELECT COUNT(*) FROM connection_firewall_log WHERE action='BLOCKED'").fetchone()[0]

            storage_usage = self.get_local_storage_usage()
            storage_cap = self.config.get("storage_allocation_mb", 500)
            
            return {
                "version": self.current_version,
                "release_channel": self.config.get("release_channel", "BETA"),
                "feature_flags": self.config.get("feature_flags", {}),
                "wallet": {"address": user_addr, "fox": fox, "sats": sats},
                "reserves": {"fox": ra, "sats": rb},
                "utxo_count": utxo_count,
                "blocked_connections": blocked_conn,
                "storage": {"used_mb": storage_usage, "cap_mb": storage_cap},
                "flags": self.query_system_flags()
            }
