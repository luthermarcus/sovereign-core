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
        self.db_path = os.path.expanduser(self.config.get("db_path", "~/node-stack/sovereign_os_v274.db"))
        self.backup_dir = os.path.expanduser("~/sovereign-ecosystem/backups")
        self.media_dir = os.path.expanduser("~/sovereign-ecosystem/media_cache")
        self.mail_dir = os.path.expanduser("~/sovereign-ecosystem/mail")
        self.vault_path = os.path.expanduser("~/sovereign-ecosystem/vault/master.key")
        self.auth_cookie_path = os.path.expanduser("~/sovereign-ecosystem/vault/rpc_auth.cookie")
        self.bound_rest_port = None
        self.current_version = "v2.7.4"

        self._init_security_vaults()
        self.run_preflight_checks()
        self.init_database()
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

    def run_preflight_checks(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.media_dir, exist_ok=True)
        os.makedirs(self.mail_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()
            if not res or res[0] != "ok":
                print(f"[!] Pre-flight storage warning: {res}")
        except Exception as e:
            print(f"[!] Pre-flight error: {e}")
        finally:
            conn.close()

    def init_database(self):
        with self.get_conn() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS accounts (address TEXT PRIMARY KEY, cipher_payload TEXT, balance REAL CHECK(balance >= 0))")
            conn.execute("CREATE TABLE IF NOT EXISTS liquidity_pools (pool_id TEXT PRIMARY KEY, reserve_a REAL, reserve_b REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS system_flags (flag_key TEXT PRIMARY KEY, level TEXT, status TEXT, message TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS network_peers (peer_id TEXT PRIMARY KEY, ip_address TEXT, status TEXT, ping_ms REAL, banscore INTEGER, last_seen REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS transaction_ledger (tx_id TEXT PRIMARY KEY, type TEXT, amount REAL, fee REAL, counterparty TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS cross_chain_bridge (swap_id TEXT PRIMARY KEY, amount REAL, preimage_hash TEXT, status TEXT, expires_at REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS trusted_contacts (address TEXT PRIMARY KEY, alias TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS media_registry (track_id TEXT PRIMARY KEY, title TEXT, artist TEXT, ipfs_hash TEXT, size_mb REAL, downloaded INTEGER)")
            conn.execute("CREATE TABLE IF NOT EXISTS web3_mail (mail_id TEXT PRIMARY KEY, sender TEXT, subject TEXT, body TEXT, timestamp REAL, is_read INTEGER)")

            conn.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01', ?, 250.0)", (base64.b64encode(b"user").decode(),))
            conn.execute("INSERT OR IGNORE INTO accounts VALUES ('user_wallet_01_sats', ?, 50000.0)", (base64.b64encode(b"sats").decode(),))
            conn.execute("INSERT OR IGNORE INTO liquidity_pools VALUES ('MAIN_POOL', 10000.0, 500000.0)")
            conn.execute("INSERT OR IGNORE INTO trusted_contacts VALUES ('0xVerifiedColdStorage', 'Primary Vault')")
            conn.execute("INSERT OR IGNORE INTO media_registry VALUES ('track_01', 'Genesis Block Symphony', 'Satoshi Sound', 'QmHashGenesis123', 4.2, 1)")
            conn.execute("INSERT OR IGNORE INTO web3_mail VALUES ('mail_01', 'core-node@sovereign.net', 'Submenu Dashboard Notice', 'Interactive submenus fully deployed in v2.7.4.', ?, 0)", (time.time() - 1800,))
            
            now = time.time()
            conn.execute("INSERT OR IGNORE INTO transaction_ledger VALUES ('tx_genesis', 'CREDIT', 250.0, 1.0, 'Network Faucet', ?)", (now - 3600,))
            conn.execute("INSERT OR IGNORE INTO cross_chain_bridge VALUES ('bridge_swap_01', 50.0, 'a3f8c...hash', 'LOCKED', ?)", (now + 86400,))
            conn.commit()

    def get_local_storage_usage(self):
        total_bytes = 0
        paths = [self.db_path, self.backup_dir, self.media_dir, self.mail_dir]
        for p in paths:
            if os.path.isfile(p):
                total_bytes += os.path.getsize(p)
            elif os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.exists(fp): total_bytes += os.path.getsize(fp)
        return total_bytes / (1024 * 1024)

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
            if contact:
                return {"status": "VERIFIED", "alias": contact[0]}
            return {"status": "UNVERIFIED", "warning": "WARNING: Destination address is not in your trusted contact book."}

    def add_trusted_contact(self, address, alias):
        with self.get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO trusted_contacts VALUES (?, ?)", (address, alias))
            conn.commit()
        return {"status": "SUCCESS", "message": f"Added '{alias}' to trusted address book."}

    def get_transaction_history(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT tx_id, type, amount, fee, counterparty, timestamp FROM transaction_ledger ORDER BY timestamp DESC").fetchall()

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

    def get_inbox_messages(self):
        with self.get_conn() as conn:
            return conn.execute("SELECT mail_id, sender, subject, body, timestamp, is_read FROM web3_mail ORDER BY timestamp DESC").fetchall()

    def send_encrypted_mail(self, recipient, subject, body):
        mail_id = f"mail_{int(time.time())}_{os.urandom(2).hex()}"
        now = time.time()
        local_mail_file = os.path.join(self.mail_dir, f"{mail_id}.enc")
        with open(local_mail_file, 'w') as f:
            f.write(base64.b64encode(body.encode()).decode())
        with self.get_conn() as conn:
            conn.execute("INSERT INTO web3_mail VALUES (?, ?, ?, ?, ?, 0)", (mail_id, recipient, subject, body, now))
            conn.commit()
        return {"status": "SUCCESS", "mail_id": mail_id, "recipient": recipient, "storage": "Stored Locally"}

    def send_transaction_with_fee(self, recipient, amount, fee_rate):
        auth_check = self.verify_address(recipient)
        tx_id = f"tx_{int(time.time())}_{os.urandom(2).hex()}"
        now = time.time()
        total_cost = amount + fee_rate
        with self.get_conn() as conn:
            bal = conn.execute("SELECT balance FROM accounts WHERE address='user_wallet_01'").fetchone()[0]
            if bal < total_cost:
                return {"status": "ERROR", "message": f"Insufficient funds. Required: {total_cost} FOX"}
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
            if bal < amount:
                return {"status": "ERROR", "message": "Insufficient funds for bridge lock."}
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE address='user_wallet_01'", (amount,))
            conn.execute("INSERT INTO cross_chain_bridge VALUES (?, ?, ?, 'LOCKED', ?)", (swap_id, amount, preimage_hash, now + 86400))
            conn.commit()
        return {"status": "LOCKED", "swap_id": swap_id, "target_chain": target_chain, "preimage_secret": preimage, "hash": preimage_hash}

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
            peers = conn.execute("SELECT COUNT(*) FROM network_peers WHERE status='ACTIVE'").fetchone()[0]
            bridges = conn.execute("SELECT COUNT(*) FROM cross_chain_bridge WHERE status='LOCKED'").fetchone()[0]
            media_count = conn.execute("SELECT COUNT(*) FROM media_registry WHERE downloaded = 1").fetchone()[0]
            mail_count = conn.execute("SELECT COUNT(*) FROM web3_mail WHERE is_read = 0").fetchone()[0]
            storage_usage = self.get_local_storage_usage()
            storage_cap = self.config.get("storage_allocation_mb", 500)
            
            return {
                "version": self.current_version,
                "release_channel": self.config.get("release_channel", "BETA"),
                "wallet": {"address": "user_wallet_01", "fox": fox, "sats": sats},
                "reserves": {"fox": ra, "sats": rb},
                "bridge_locked": bridges,
                "media_downloaded": media_count,
                "unread_mail": mail_count,
                "storage": {"used_mb": storage_usage, "cap_mb": storage_cap},
                "flags": self.query_system_flags()
            }
