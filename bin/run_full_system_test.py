#!/usr/bin/env python3
import os, sys, sqlite3, json, time, urllib.request, logging

logging.basicConfig(
    filename=os.path.expanduser('~/sovereign-ecosystem/logs/system_test.log'),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode, load_manifest

def run_tests():
    print("[*] Initializing Sovereign Core Comprehensive Test Runner (v2.8.5)...")
    node = SovereignNode()
    passed = 0
    failed = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            print(f"  [✓] PASS: {name}")
            logging.info(f"PASS: {name} - {details}")
            passed += 1
        else:
            print(f"  [✗] FAIL: {name} ({details})")
            logging.error(f"FAIL: {name} - {details}")
            failed += 1

    print("\n--- [1] SQLite WAL & Database Integrity Tests ---")
    with node.get_conn() as conn:
        res = conn.execute("PRAGMA integrity_check;").fetchone()
        assert_test("Database Integrity OK", res and res[0] == "ok", str(res))
        wal = conn.execute("PRAGMA journal_mode;").fetchone()
        assert_test("WAL Journal Mode Active", wal and wal[0].lower() == "wal", str(wal))

    print("\n--- [2] Wallet & Transfer Tests ---")
    with node.get_conn() as conn:
        bal = conn.execute("SELECT balance FROM accounts WHERE address='user_wallet_01'").fetchone()[0]
        assert_test("User Wallet Balance Initialized", bal >= 250.0, f"Balance: {bal}")
    
    tx_res = node.send_transaction_with_fee("0xVerifiedColdStorage", 10.0, 0.5)
    assert_test("Protected Transfer Executed", tx_res["status"] == "SUCCESS", str(tx_res))

    print("\n--- [3] HTLC Cross-Chain Bridge Tests ---")
    bridge_res = node.initiate_htlc_bridge(20.0, "EVM-L2")
    assert_test("HTLC Bridge Lock Created", bridge_res["status"] == "LOCKED", str(bridge_res))

    print("\n--- [4] Web3 Encrypted Mail & Storage Tests ---")
    mail_res = node.send_encrypted_mail("node-peer@sovereign.net", "Test Subject", "Automated test message.")
    assert_test("Encrypted Mail Dispatched", mail_res["status"] == "SUCCESS", str(mail_res))
    inbox = node.get_inbox_messages()
    assert_test("Inbox Contains Messages", len(inbox) > 0, f"Total mail: {len(inbox)}")

    print("\n--- [5] IPFS Media Catalog & Sync Tests ---")
    catalog = node.get_media_catalog()
    assert_test("Media Catalog Populated", len(catalog) > 0, f"Tracks: {len(catalog)}")
    dl_res = node.download_media_track("track_01")
    assert_test("Media Track Downloaded Locally", dl_res["status"] == "SUCCESS", str(dl_res))

    print("\n--- [6] P2P Mesh & Version Signaling Tests ---")
    peers = node.get_network_peers()
    assert_test("Network Peers Registered", len(peers) > 0, f"Peers: {len(peers)}")
    signal_res = node.broadcast_update_signal_to_outdated()
    assert_test("Outdated Peer Update Signaling", signal_res["status"] == "SUCCESS", str(signal_res))

    print("\n--- [7] Feature Flag & Options Manual Tests ---")
    manifest_data = load_manifest()
    assert_test("Fork Manifest Loaded", "feature_flags" in manifest_data, str(manifest_data.get("feature_flags")))
    toggle_res = node.toggle_feature_flag("beta_telemetry_enabled")
    assert_test("Feature Flag Toggled Successfully", toggle_res["status"] == "SUCCESS", str(toggle_res))

    print("\n--- [8] Community Feedback & Issue Matrix Tests ---")
    fb_res = node.submit_pinpointed_suggestion("[SQLite WAL]", "Automated stress test verification.")
    assert_test("Pinpointed Suggestion Logged", fb_res["status"] == "SUCCESS", str(fb_res))
    all_fb = node.get_all_feedback()
    assert_test("Feedback Records Retrievable", len(all_fb) > 0, f"Feedback items: {len(all_fb)}")

    print("\n--- [9] Backup Snapshot Tests ---")
    backup_res = node.create_live_backup()
    assert_test("VACUUM INTO Backup Snapshot Created", backup_res["status"] == "SUCCESS", backup_res.get("file", ""))

    print("\n--- [10] Resilient REST API Loopback Tests ---")
    if node.bound_rest_port:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{node.bound_rest_port}/", headers={"Authorization": f"sov_rpc:{node.api_token}"})
            with urllib.request.urlopen(req, timeout=2) as response:
                assert_test("REST API Loopback Responding", response.status == 200, f"HTTP {response.status}")
        except Exception as e:
            assert_test("REST API Loopback Responding", False, str(e))
    else:
        assert_test("REST API Bound", False, "No port bound")

    print(f"\n==========================================")
    print(f"TEST RESULTS: PASSED: {passed} | FAILED: {failed}")
    print(f"Full logs written to: ~/sovereign-ecosystem/logs/system_test.log")
    print(f"==========================================")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
