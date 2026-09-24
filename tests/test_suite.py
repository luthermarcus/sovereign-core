#!/usr/bin/env python3
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from sovereign_core import SovereignNode

def run_tests():
    print("--- Running Sovereign Core Verification Suite ---")
    node = SovereignNode(is_regtest=True)
    
    # Test Overdraft Protection
    try:
        node.process_5_5_90_split('genesis_faucet', 'dev_test', 999999999.0)
        assert False, "Failed: Overdraft permitted!"
    except ValueError:
        print("✓ Balance constraint verified (Overdraft prevented)")

    # Test Proof-of-Compute uniqueness
    poc_res1 = node.record_compute_proof("test_runner")
    poc_res2 = node.record_compute_proof("test_runner")
    assert poc_res1["hash"] != poc_res2["hash"]
    print("✓ Cryptographic PoC uniqueness & commit verified")

    # Test Storage Pruning
    prune_res = node.prune_ledger(keep_days=-1)
    assert prune_res["status"] == "pruned"
    print("✓ Storage Optimizer verified")

    print("\n[PASSED] All CI/CD tests successful.")

if __name__ == '__main__':
    run_tests()
