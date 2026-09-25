#!/usr/bin/env python3
import os, json, sqlite3, hashlib, time, socket, threading, base64, glob, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

def load_manifest():
    path = os.path.expanduser("~/sovereign-ecosystem/fork_manifest.json")
    try:
        with open(path, 'r') as f: return json.load(f)
    except: return {}

class SovereignNode:
    def __init__(self):
        self.config = load_manifest()
        self.db_path = os.path.expanduser(self.config.get("db_path", "~/node-stack/sovereign_os_v297.db"))
        self.backup_dir = os.path.expanduser("~/sovereign-ecosystem/backups")
        self.media_dir = os.path.expanduser("~/sovereign-ecosystem/media_cache")
        self.mail_dir = os.path.expanduser("~/sovereign-ecosystem/mail")
        self.modules_dir = os.path.expanduser("~/sovereign-ecosystem/modules")
        self.vault_path = os.path.expanduser("~/sovereign-ecosystem/vault/master.key")
        self.auth_cookie_path = os.path.expanduser("~/sovereign-ecosystem/vault/rpc_auth.cookie")
        self.bound_rest_port = None
        self.current_version = "v2.9.7-beta"

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
        
        with self.get_conn() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS accounts (address TEXT PRIMARY KEY, cipher_payload TEXT, balance REAL CHECK(balance >= 0))")
            conn.execute("CREATE TABLE IF NOT EXISTS liquidity_pools (pool_id TEXT PRIMARY KEY, reserve_a REAL, reserve_b REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS system_flags (flag_key TEXT PRIMARY KEY, level TEXT, status TEXT, message TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS network_peers (peer_id TEXT PRIMARY KEY, ip_address TEXT, version TEXT, status TEXT, ping_ms REAL, banscore INTEGER, last_seen REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS transaction_ledger (tx_id TEXT PRIMARY KEY, type TEXT, amount REAL, fee REAL, counterparty TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS cross_chain_bridge (swap_id TEXT PRIMARY KEY, amount REAL, preimage_hash TEXT, status TEXT, expires_at REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS trusted_contacts (address TEXT PRIMARY KEY, alias TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS media_registry (track_id TEXT PRIMARY KEY, title TEXT, artist TEXT, ipfs_hash TEXT, size_mb REAL, downloaded INTEGER)")
            conn.execute("CREATE TABLE IF NOT EXISTS web3_mail (mail_id TEXT PRIMARY KEY, sender TEXT, subject TEXT, body TEXT, timestamp REAL, is_read INTEGER)")
            conn.execute("CREATE TABLE IF NOT EXISTS developer_plugins (plugin_id TEXT PRIMARY KEY, name TEXT, entrypoint TEXT, status TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS connection_firewall_log (firewall_id TEXT PRIMARY KEY, endpoint TEXT, action TEXT, reason TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS network_stress_alerts (alert_id TEXT PRIMARY KEY, peer_id TEXT, signal_type TEXT, status TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS network_knowledge_base (ecosystem_id TEXT PRIMARY KEY, endpoint TEXT, protocol_version TEXT, health_score REAL, indexed_at REAL)")

            if channel in ["BETA", "SIMULATION", "DEV"]:
                conn.execute("CREATE TABLE IF NOT EXISTS beta_telemetry_feedback (feedback_id TEXT PRIMARY KEY, subsystem TEXT, comments TEXT, status TEXT, timestamp REAL)")
                conn.execute("INSERT OR IGNORE INTO beta_telemetry_feedback VALUES ('fb_init', '[Knowledge Crawler]', 'Standalone crawler module active in v2.9.7.', 'OPEN', ?)", (time.time(),))
            else:
                conn.execute("DROP TABLE IF EXISTS beta_telemetry_feedback;")
                conn.execute("DROP TABLE IF EXISTS connection_firewall_log;")
                conn.execute("DROP TABLE IF EXISTS network_stress_alerts;")
                conn.execute("DROP TABLE IF EXISTS network_knowledge_base;")

            # Seed default data
            conn.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01', ?, 250.0)", (base64.b64encode(b"user").decode(),))
            conn.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01_sats', ?, 50000.0)", (base64.b64encode(b"sats").decode(),))
            conn.execute("INSERT OR IGNORE INTO liquidity_pools VALUES ('MAIN_POOL', 10000.0, 500000.0)")
            conn.execute("INSERT OR IGNORE INTO trusted_contacts VALUES ('0xVerifiedColdStorage', 'Primary Vault')")
            conn.execute("INSERT OR IGNORE INTO media_registry VALUES ('track_01', 'Genesis Block Symphony', 'Satoshi Sound', 'QmHashGenesis123', 4.2, 1)")
            conn.execute("INSERT OR IGNORE INTO developer_plugins VALUES ('plugin_sandbox_01', 'Core Debugger', 'debug.py', 'ACTIVE')")
            
            now = time.time()
            conn.execute("INSERT OR IGNORE INTO network_peers VALUES ('peer_node_alpha', '10.0.0.1', 'v2.9.7-beta', 'ACTIVE', 12.5, 0, ?)", (now,))
            conn.execute("INSERT OR IGNORE INTO connection_firewall_log VALUES ('fw_sample_01', '198.51.100.42:9050', 'BLOCKED', 'Untrusted external scraper IP blocked by Sovereign Firewall.', ?)", (now - 300,))
            conn.execute("INSERT OR IGNORE INTO network_knowledge_base VALUES ('ecosystem_alpha_hub', '10.0.0.15:8080', 'v2.9.7-beta', 98.5, ?)", (now,))
            conn.commit()

    def get_knowledge_base_entries(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT ecosystem_id, endpoint, protocol_version, health_score FROM network_knowledge_base").fetchall()

    def run_crawler_subprocess(self):
        crawler_path = os.path.expanduser("~/sovereign-ecosystem/bin/sovereign_crawler.py")
        try:
            res = subprocess.run(["python3", crawler_path], capture_output=True, text=True, timeout=10)
            return {"status": "SUCCESS", "output": res.stdout.strip()}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def get_local_storage_usage(self):
        total_bytes = 0
        stack_dir = os.path.expanduser("~/node-stack")
        if os.path.isdir(stack_dir):
            for root, dirs, files in os.walk(stack_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp): total_bytes += os.path.getsize(fp)
        return total_bytes / (1024 * 1024)

    def get_network_peers(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT peer_id, ip_address, version, status, ping_ms FROM network_peers").fetchall()

    def get_firewall_logs(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT firewall_id, endpoint, action, reason, timestamp FROM connection_firewall_log ORDER BY timestamp DESC").fetchall()

    def whitelist_firewall_endpoint(self, endpoint):
        with self.get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO connection_firewall_log VALUES (?, ?, 'WHITELISTED', 'User manually approved connection.', ?)", (f"fw_wl_{int(time.time())}", endpoint, time.time()))
            conn.commit()
        return {"status": "SUCCESS", "message": f"Endpoint {endpoint} successfully whitelisted."}

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

    def verify_address(self, target_address):
        with self.get_conn() as conn:
            contact = conn.execute("SELECT alias FROM trusted_contacts WHERE address = ?", (target_address,)).fetchone()
            if contact: return {"status": "VERIFIED", "alias": contact[0]}
            return {"status": "UNVERIFIED", "warning": "WARNING: Destination address is not in your trusted contact book."}

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
            
            peer_rows = conn.execute("SELECT version FROM network_peers").fetchall()
            total_peers = len(peer_rows)
            outdated_peers = sum(1 for p in peer_rows if p[0] != self.current_version)

            knowledge_count = 0
            blocked_conn = 0
            try:
                knowledge_count = conn.execute("SELECT COUNT(*) FROM network_knowledge_base").fetchone()[0]
                blocked_conn = conn.execute("SELECT COUNT(*) FROM connection_firewall_log WHERE action='BLOCKED'").fetchone()[0]
            except: pass

            storage_usage = self.get_local_storage_usage()
            storage_cap = self.config.get("storage_allocation_mb", 500)
            
            return {
                "version": self.current_version,
                "release_channel": self.config.get("release_channel", "BETA"),
                "feature_flags": self.config.get("feature_flags", {}),
                "wallet": {"address": "user_wallet_01", "fox": fox, "sats": sats},
                "reserves": {"fox": ra, "sats": rb},
                "bridge_locked": bridges,
                "total_peers": total_peers,
                "outdated_peers": outdated_peers,
                "indexed_ecosystems": knowledge_count,
                "blocked_connections": blocked_conn,
                "storage": {"used_mb": storage_usage, "cap_mb": storage_cap},
                "flags": self.query_system_flags()
            }
