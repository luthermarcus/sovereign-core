#!/usr/bin/env python3
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from sovereign_core import SovereignNode

def run_tests():
    print("--- Running Sovereign Core v0.2.5 IoT Verification Suite ---")
    node = SovereignNode(is_regtest=True)
    # Test batcher
    node.process_batched_micro_payment('genesis_faucet', 'test_user', 10.0)
    # Test self-healing doctor
    report = node.doctor.run_health_check_and_heal()
    assert report["status"] == "OPTIMAL"
    print("✓ Autonomous self-healing & micro-batching tests passed successfully.")

if __name__ == '__main__':
    run_tests()
