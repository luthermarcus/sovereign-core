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
        self.db_path = os.path.expanduser(self.config.get("db_path", "~/node-stack/sovereign_os_v285.db"))
        self.backup_dir = os.path.expanduser("~/sovereign-ecosystem/backups")
        self.media_dir = os.path.expanduser("~/sovereign-ecosystem/media_cache")
        self.mail_dir = os.path.expanduser("~/sovereign-ecosystem/mail")
        self.modules_dir = os.path.expanduser("~/sovereign-ecosystem/modules")
        self.vault_path = os.path.expanduser("~/sovereign-ecosystem/vault/master.key")
        self.auth_cookie_path = os.path.expanduser("~/sovereign-ecosystem/vault/rpc_auth.cookie")
        self.bound_rest_port = None
        self.current_version = "v2.8.5-beta"

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
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
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

            if channel in ["BETA", "SIMULATION", "DEV"]:
                conn.execute("CREATE TABLE IF NOT EXISTS beta_telemetry_feedback (feedback_id TEXT PRIMARY KEY, subsystem TEXT, comments TEXT, status TEXT, timestamp REAL)")
                conn.execute("INSERT OR IGNORE INTO beta_telemetry_feedback VALUES ('fb_init', '[Core Engine]', 'All methods restored in v2.8.5.', 'OPEN', ?)", (time.time(),))
            else:
                conn.execute("DROP TABLE IF EXISTS beta_telemetry_feedback;")

            # Seed default data
            conn.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01', ?, 250.0)", (base64.b64encode(b"user").decode(),))
            conn.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01_sats', ?, 50000.0)", (base64.b64encode(b"sats").decode(),))
            conn.execute("INSERT OR IGNORE INTO liquidity_pools VALUES ('MAIN_POOL', 10000.0, 500000.0)")
            conn.execute("INSERT OR IGNORE INTO trusted_contacts VALUES ('0xVerifiedColdStorage', 'Primary Vault')")
            conn.execute("INSERT OR IGNORE INTO media_registry VALUES ('track_01', 'Genesis Block Symphony', 'Satoshi Sound', 'QmHashGenesis123', 4.2, 1)")
            conn.execute("INSERT OR IGNORE INTO developer_plugins VALUES ('plugin_sandbox_01', 'Core Debugger', 'debug.py', 'ACTIVE')")
            
            now = time.time()
            conn.execute("INSERT OR IGNORE INTO network_peers VALUES ('peer_node_alpha', '10.0.0.1', 'v2.8.5-beta', 'ACTIVE', 12.5, 0, ?)", (now,))
            conn.execute("INSERT OR IGNORE INTO network_peers VALUES ('peer_node_beta', '10.0.0.2', 'v2.7.4', 'OUTDATED', 18.2, 0, ?)", (now,))
            
            conn.execute("INSERT OR IGNORE INTO transaction_ledger VALUES ('tx_genesis', 'CREDIT', 250.0, 1.0, 'Network Faucet', ?)", (now - 3600,))
            conn.commit()

    def get_local_storage_usage(self):
        total_bytes = 0
        paths = [self.db_path, self.backup_dir, self.media_dir, self.mail_dir, self.modules_dir]
        for p in paths:
            if os.path.isfile(p): total_bytes += os.path.getsize(p)
            elif os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.exists(fp): total_bytes += os.path.getsize(fp)
        return total_bytes / (1024 * 1024)

    # --- RESTORED HELPER METHODS ---
    def send_encrypted_mail(self, recipient, subject, body):
        mail_id = f"mail_{int(time.time())}_{os.urandom(2).hex()}"
        now = time.time()
        with self.get_conn() as conn:
            conn.execute("INSERT INTO web3_mail VALUES (?, ?, ?, ?, ?, 0)", (mail_id, recipient, subject, body, now))
            conn.commit()
        return {"status": "SUCCESS", "mail_id": mail_id, "recipient": recipient}

    def get_inbox_messages(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT mail_id, sender, subject, body, timestamp, is_read FROM web3_mail ORDER BY timestamp DESC").fetchall()

    def get_media_catalog(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT track_id, title, artist, ipfs_hash, size_mb, downloaded FROM media_registry").fetchall()

    def download_media_track(self, track_id):
        with self.get_conn() as conn:
            row = conn.execute("SELECT title, artist FROM media_registry WHERE track_id = ?", (track_id,)).fetchone()
            if not row: return {"status": "ERROR", "message": "Track not found."}
            conn.execute("UPDATE media_registry SET downloaded = 1 WHERE track_id = ?", (track_id,))
            conn.commit()
            fake_file = os.path.join(self.media_dir, f"{track_id}.mp3")
            with open(fake_file, 'w') as f: f.write("DECENTRALIZED_AUDIO_STREAM_DATA")
        return {"status": "SUCCESS", "track": row[0], "artist": row[1], "path": fake_file}

    def get_network_peers(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT peer_id, ip_address, version, status, ping_ms FROM network_peers").fetchall()

    def broadcast_update_signal_to_outdated(self):
        with self.get_conn() as conn:
            outdated = conn.execute("SELECT peer_id, version FROM network_peers WHERE version != ?", (self.current_version,)).fetchall()
            for peer_id, ver in outdated:
                conn.execute("UPDATE network_peers SET status = 'UPDATE_SIGNALED' WHERE peer_id = ?", (peer_id,))
            conn.commit()
        return {"status": "SUCCESS", "signaled_count": len(outdated), "message": f"Broadcast update signal for {self.current_version} to outdated peers."}

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

    def submit_pinpointed_suggestion(self, subsystem, comments):
        feedback_id = f"fb_{int(time.time())}_{os.urandom(2).hex()}"
        now = time.time()
        with self.get_conn() as conn:
            conn.execute("INSERT INTO beta_telemetry_feedback VALUES (?, ?, ?, 'OPEN', ?)", (feedback_id, subsystem, comments, now))
            conn.commit()
        return {"status": "SUCCESS", "message": f"Suggestion pinpointed to {subsystem} successfully!"}

    def get_all_feedback(self):
        with self.get_conn() as conn:
            try:
                return conn.execute("SELECT feedback_id, subsystem, comments, status, timestamp FROM beta_telemetry_feedback ORDER BY timestamp DESC").fetchall()
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
            plugin_count = conn.execute("SELECT COUNT(*) FROM developer_plugins WHERE status='ACTIVE'").fetchone()[0]
            
            peer_rows = conn.execute("SELECT version FROM network_peers").fetchall()
            total_peers = len(peer_rows)
            outdated_peers = sum(1 for p in peer_rows if p[0] != self.current_version)

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
                "storage": {"used_mb": storage_usage, "cap_mb": storage_cap},
                "flags": self.query_system_flags()
            }
