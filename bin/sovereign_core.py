#!/usr/bin/env python3
import os, json, sqlite3, hashlib, time, socket, threading, base64
from http.server import BaseHTTPRequestHandler, HTTPServer

def load_manifest():
    path = os.path.expanduser("~/sovereign-ecosystem/fork_manifest.json")
    try:
        with open(path, 'r') as f: return json.load(f)
    except: return {}

class SovereignNode:
    def __init__(self):
        self.config = load_manifest()
        self.db_path = os.path.expanduser(self.config.get("db_path", "~/node-stack/sovereign_os_v281.db"))
        self.backup_dir = os.path.expanduser("~/sovereign-ecosystem/backups")
        self.media_dir = os.path.expanduser("~/sovereign-ecosystem/media_cache")
        self.mail_dir = os.path.expanduser("~/sovereign-ecosystem/mail")
        self.modules_dir = os.path.expanduser("~/sovereign-ecosystem/modules")
        self.vault_path = os.path.expanduser("~/sovereign-ecosystem/vault/master.key")
        self.auth_cookie_path = os.path.expanduser("~/sovereign-ecosystem/vault/rpc_auth.cookie")
        self.bound_rest_port = None
        self.current_version = "v2.8.1-beta"

        self._init_security_vaults()
        self.run_autonomous_diagnostics_and_pruning()
        self.start_resilient_rest_api()
        self.start_autonomous_watchdog()

    def _init_security_vaults(self):
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
        if not os.path.exists(self.vault_path):
            with open(self.vault_path, 'w') as f: f.write(os.urandom(32).hex())
        with open(self.vault_path, 'r') as f: self.master_key = f.read().strip()
        
        self.api_token = os.urandom(32).hex()
        with open(self.auth_cookie_path, 'w') as f: f.write(f"sov_rpc:{self.api_token}")

    def get_conn(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA mmap_size = 268435456;")
        conn.execute("PRAGMA temp_store = MEMORY;")
        return conn

    def run_autonomous_diagnostics_and_pruning(self):
        """Self-healing boot inspector with conditional beta telemetry pruning for live releases."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.media_dir, exist_ok=True)
        os.makedirs(self.mail_dir, exist_ok=True)
        os.makedirs(self.modules_dir, exist_ok=True)
        
        channel = self.config.get("release_channel", "BETA")
        
        with self.get_conn() as conn:
            # Core tables
            conn.execute("CREATE TABLE IF NOT EXISTS accounts (address TEXT PRIMARY KEY, cipher_payload TEXT, balance REAL CHECK(balance >= 0))")
            conn.execute("CREATE TABLE IF NOT EXISTS liquidity_pools (pool_id TEXT PRIMARY KEY, reserve_a REAL, reserve_b REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS system_flags (flag_key TEXT PRIMARY KEY, level TEXT, status TEXT, message TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS network_peers (peer_id TEXT PRIMARY KEY, ip_address TEXT, status TEXT, ping_ms REAL, banscore INTEGER, last_seen REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS transaction_ledger (tx_id TEXT PRIMARY KEY, type TEXT, amount REAL, fee REAL, counterparty TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS cross_chain_bridge (swap_id TEXT PRIMARY KEY, amount REAL, preimage_hash TEXT, status TEXT, expires_at REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS trusted_contacts (address TEXT PRIMARY KEY, alias TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS media_registry (track_id TEXT PRIMARY KEY, title TEXT, artist TEXT, ipfs_hash TEXT, size_mb REAL, downloaded INTEGER)")
            conn.execute("CREATE TABLE IF NOT EXISTS web3_mail (mail_id TEXT PRIMARY KEY, sender TEXT, subject TEXT, body TEXT, timestamp REAL, is_read INTEGER)")
            conn.execute("CREATE TABLE IF NOT EXISTS developer_plugins (plugin_id TEXT PRIMARY KEY, name TEXT, entrypoint TEXT, status TEXT)")

            # Conditional Beta Telemetry vs Live Pruning
            if channel in ["BETA", "SIMULATION", "DEV"]:
                conn.execute("CREATE TABLE IF NOT EXISTS beta_telemetry_feedback (feedback_id TEXT PRIMARY KEY, category TEXT, comments TEXT, timestamp REAL)")
                conn.execute("INSERT OR IGNORE INTO beta_telemetry_feedback VALUES ('fb_init', 'SYSTEM', 'Telemetry feedback loop initialized for beta testing.', ?)", (time.time(),))
            else:
                # AUTO-PRUNE: Drop beta tables if node goes LIVE / MAINNET
                conn.execute("DROP TABLE IF EXISTS beta_telemetry_feedback;")

            # Seed default fixtures
            conn.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01', ?, 250.0)", (base64.b64encode(b"user").decode(),))
            conn.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01_sats', ?, 50000.0)", (base64.b64encode(b"sats").decode(),))
            conn.execute("INSERT OR IGNORE INTO liquidity_pools VALUES ('MAIN_POOL', 10000.0, 500000.0)")
            conn.execute("INSERT OR IGNORE INTO trusted_contacts VALUES ('0xVerifiedColdStorage', 'Primary Vault')")
            conn.execute("INSERT OR IGNORE INTO media_registry VALUES ('track_01', 'Genesis Block Symphony', 'Satoshi Sound', 'QmHashGenesis123', 4.2, 1)")
            conn.execute("INSERT OR IGNORE INTO developer_plugins VALUES ('plugin_sandbox_01', 'Core Debugger', 'debug.py', 'ACTIVE')")
            conn.execute("INSERT OR IGNORE INTO network_peers VALUES ('peer_bootstrap_01', '10.0.0.1', 'ACTIVE', 12.5, 0, ?)", (time.time(),))
            
            now = time.time()
            conn.execute("INSERT OR IGNORE INTO transaction_ledger VALUES ('tx_genesis', 'CREDIT', 250.0, 1.0, 'Network Faucet', ?)", (now - 3600,))
            conn.commit()

    def get_local_storage_usage(self):
        total_bytes = 0
        paths = [self.db_path, self.backup_dir, self.media_dir, self.mail_dir, self.modules_dir]
        for p in paths:
            if os.path.isfile(p):
                total_bytes += os.path.getsize(p)
            elif os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.exists(fp): total_bytes += os.path.getsize(fp)
        return total_bytes / (1024 * 1024)

    def submit_community_feedback(self, category, comments):
        """Allows community testers to submit improvement ideas during the beta phase."""
        if self.config.get("release_channel", "BETA") not in ["BETA", "SIMULATION", "DEV"]:
            return {"status": "DISABLED", "message": "Telemetry feedback is pruned on live production nodes."}
        
        feedback_id = f"fb_{int(time.time())}_{os.urandom(2).hex()}"
        now = time.time()
        with self.get_conn() as conn:
            conn.execute("INSERT INTO beta_telemetry_feedback VALUES (?, ?, ?, ?)", (feedback_id, category, comments, now))
            conn.commit()
        return {"status": "SUCCESS", "feedback_id": feedback_id, "message": "Feedback recorded. Thank you for helping improve Sovereign Core!"}

    def get_all_feedback(self):
        with self.get_conn() as conn:
            try:
                return conn.execute("SELECT feedback_id, category, comments, timestamp FROM beta_telemetry_feedback ORDER BY timestamp DESC").fetchall()
            except sqlite3.OperationalError:
                return []

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

    def get_loaded_plugins(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT plugin_id, name, entrypoint, status FROM developer_plugins").fetchall()

    def get_network_peers(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT peer_id, ip_address, status, ping_ms, banscore FROM network_peers").fetchall()

    def create_live_backup(self):
        os.makedirs(self.backup_dir, exist_ok=True)
        backup_file = os.path.join(self.backup_dir, f"sovereign_backup_{int(time.time())}.db")
        try:
            with self.get_conn() as conn:
                conn.execute(f"VACUUM INTO '{backup_file}'")
            return {"status": "SUCCESS", "file": backup_file}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def verify_address(self, target_address):
        with self.get_conn() as conn:
            contact = conn.execute("SELECT alias FROM trusted_contacts WHERE address = ?", (target_address,)).fetchone()
            if contact: return {"status": "VERIFIED", "alias": contact[0]}
            return {"status": "UNVERIFIED", "warning": "WARNING: Destination address is not in your trusted contact book."}

    def add_trusted_contact(self, address, alias):
        with self.get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO trusted_contacts VALUES (?, ?)", (address, alias))
            conn.commit()
        return {"status": "SUCCESS", "message": f"Added '{alias}' to trusted address book."}

    def get_transaction_history(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT tx_id, type, amount, fee, counterparty, timestamp FROM transaction_ledger ORDER BY timestamp DESC").fetchall()

    def send_transaction_with_fee(self, recipient, amount, fee_rate):
        auth_check = self.verify_address(recipient)
        tx_id = f"tx_{int(time.time())}_{os.urandom(2).hex()}"
        now = time.time()
        total_cost = amount + fee_rate
        with self.get_conn() as conn:
            bal = conn.execute("SELECT balance FROM accounts WHERE address='user_wallet_01'").fetchone()[0]
            if bal < total_cost: return {"status": "ERROR", "message": f"Insufficient funds. Required: {total_cost} FOX"}
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE address='user_wallet_01'", (total_cost,))
            conn.execute("INSERT OR IGNORE INTO accounts VALUES (?, ?, 0.0)", (recipient, base64.b64encode(b"recipient").decode()))
            conn.execute("UPDATE accounts SET balance = balance + ? WHERE address = ?", (amount, recipient))
            conn.execute("INSERT INTO transaction_ledger VALUES (?, 'DEBIT', ?, ?, ?, ?)", (tx_id, amount, fee_rate, recipient, now))
            conn.commit()
        return {"status": "SUCCESS", "tx_id": tx_id, "amount": amount, "fee": fee_rate, "recipient": recipient, "security_check": auth_check}

    def initiate_htlc_bridge(self, amount, target_chain):
        swap_id = f"bridge_{int(time.time())}_{os.urandom(2).hex()}"
        preimage = os.urandom(32).hex()
        preimage_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
        now = time.time()
        with self.get_conn() as conn:
            bal = conn.execute("SELECT balance FROM accounts WHERE address='user_wallet_01'").fetchone()[0]
            if bal < amount: return {"status": "ERROR", "message": "Insufficient funds for bridge lock."}
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE address='user_wallet_01'", (amount,))
            conn.execute("INSERT INTO cross_chain_bridge VALUES (?, ?, ?, 'LOCKED', ?)", (swap_id, amount, preimage_hash, now + 86400))
            conn.commit()
        return {"status": "LOCKED", "swap_id": swap_id, "target_chain": target_chain, "hash": preimage_hash}

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
        with self.get_conn() as conn:
            ra, rb = conn.execute("SELECT reserve_a, reserve_b FROM liquidity_pools WHERE pool_id = 'MAIN_POOL'").fetchone()
            fox = conn.execute("SELECT balance FROM accounts WHERE address='user_wallet_01'").fetchone()[0]
            sats = conn.execute("SELECT balance FROM accounts WHERE address='user_wallet_01_sats'").fetchone()[0]
            bridges = conn.execute("SELECT COUNT(*) FROM cross_chain_bridge WHERE status='LOCKED'").fetchone()[0]
            plugin_count = conn.execute("SELECT COUNT(*) FROM developer_plugins WHERE status='ACTIVE'").fetchone()[0]
            peer_count = conn.execute("SELECT COUNT(*) FROM network_peers WHERE status='ACTIVE'").fetchone()[0]
            
            feedback_count = 0
            try:
                feedback_count = conn.execute("SELECT COUNT(*) FROM beta_telemetry_feedback").fetchone()[0]
            except: pass

            storage_usage = self.get_local_storage_usage()
            storage_cap = self.config.get("storage_allocation_mb", 500)
            
            return {
                "version": self.current_version,
                "release_channel": self.config.get("release_channel", "BETA"),
                "wallet": {"address": "user_wallet_01", "fox": fox, "sats": sats},
                "reserves": {"fox": ra, "sats": rb},
                "bridge_locked": bridges,
                "active_plugins": plugin_count,
                "active_peers": peer_count,
                "beta_feedback_records": feedback_count,
                "storage": {"used_mb": storage_usage, "cap_mb": storage_cap},
                "flags": self.query_system_flags()
            }
