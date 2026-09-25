#!/usr/bin/env python3
import os, sys, sqlite3, json, time, urllib.request, logging

# Robust log path resolution for container & bare-metal environments
log_dir = '/app/logs' if os.path.exists('/app') else os.path.expanduser('~/sovereign-ecosystem/logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'system_test.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode, load_manifest

def run_tests():
    print("[*] Initializing Sovereign Core Stress Benchmark & Test Suite (v2.8.9)...")
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

    print("\n--- [2] Stress Benchmark & Circuit Breaker Tests ---")
    start_time = time.time()
    stress_success = True
    iterations = 50
    try:
        with node.get_conn() as conn:
            for i in range(iterations):
                # Check storage circuit breaker (90% cap guard)
                usage = node.get_local_storage_usage()
                cap = node.config.get("storage_allocation_mb", 500)
                if usage > (cap * 0.9):
                    raise Exception("STORAGE_CIRCUIT_BREAKER_TRIPPED: Storage exceeded 90% threshold.")
                conn.execute("INSERT OR REPLACE INTO system_flags VALUES (?, 'INFO', 'ACTIVE', 'Stress benchmark ping', ?)", (f"bench_{i}", time.time()))
            conn.commit()
    except Exception as e:
        stress_success = False
        logging.error(f"Stress test halted by circuit breaker: {e}")

    duration = time.time() - start_time
    tps = iterations / (duration if duration > 0 else 0.001)
    assert_test("High-Frequency Transaction Circuit Breaker Test", stress_success, f"Processed {iterations} ops in {duration:.3f}s ({tps:.1f} ops/sec)")

    print("\n--- [3] Wallet & Transfer Tests ---")
    tx_res = node.send_transaction_with_fee("0xVerifiedColdStorage", 5.0, 0.2)
    assert_test("Protected Transfer Executed", tx_res["status"] == "SUCCESS", str(tx_res))

    print("\n--- [4] HTLC Cross-Chain Bridge Tests ---")
    bridge_res = node.initiate_htlc_bridge(10.0, "EVM-L2")
    assert_test("HTLC Bridge Lock Created", bridge_res["status"] == "LOCKED", str(bridge_res))

    print("\n--- [5] Backup Snapshot Tests ---")
    backup_res = node.create_live_backup()
    assert_test("VACUUM INTO Backup Snapshot Created", backup_res["status"] == "SUCCESS", backup_res.get("file", ""))

    print(f"\n==========================================")
    print(f"TEST RESULTS: PASSED: {passed} | FAILED: {failed}")
    print(f"Full logs written to: {log_file}")
    print(f"==========================================")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
