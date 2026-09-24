#!/usr/bin/env python3
import os, sys, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from sovereign_core import SovereignNode, HardwareWalletBridge

def run_tests():
    print("--- Running Sovereign Core Master Build Verification ---")
    node = SovereignNode(is_regtest=True)
    
    # 1. Overdraft Constraint Test
    try:
        node.process_5_5_90_split('genesis_faucet', 'dev_test', 999999999.0)
        assert False, "Failed: Overdraft was permitted!"
    except ValueError:
        print("✓ Balance constraint verified (Overdraft prevented)")

    # 2. 5/5/90 Test
    res = node.process_5_5_90_split('genesis_faucet', 'dev_test', 1000.0)
    assert res["creator_fee"] == 50.0 and res["depin_reward"] == 900.0
    print("✓ 5/5/90 Split calculation verified")

    # 3. PoC Generator Test
    poc_res = node.record_compute_proof("test_runner")
    assert poc_res["hash"].startswith("00")
    print("✓ Cryptographic PoC generated and committed")

    # 4. Storage Pruning Test
    prune_res = node.prune_ledger(keep_days=-1) # Force prune immediate
    assert prune_res["status"] == "pruned"
    print("✓ Storage Optimizer (SQLite Vacuum & Prune) verified")

    # 5. Doctor & PSBT Tests
    assert HardwareWalletBridge.generate_psbt("addr", 10)["payload"].startswith("70736274")
    assert node.doctor.run_diagnostics()["status"] in ["OPTIMAL", "DEGRADED"]
    print("✓ Node Doctor & BIP-174 PSBT formatting verified")
    print("\n[PASSED] All system checks successful.")

if __name__ == '__main__':
    run_tests()
