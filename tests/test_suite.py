#!/usr/bin/env python3
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from sovereign_core import SovereignNode, HardwareTelemetry

def run_tests():
    print("--- Running Sovereign Core v0.3.7 Verification Suite ---")
    node = SovereignNode()
    
    # Verify Mining Service
    proof = node.mine_depin_proof()
    assert proof["status"] == "success"
    print(f"✓ DePIN mining service verified (Hash: {proof['hash'][:10]}...)")

    # Verify Hardware Telemetry
    metrics = HardwareTelemetry.get_metrics()
    assert "tier" in metrics
    print(f"✓ Hardware telemetry verified ({metrics['tier']})")
    print("\n[PASSED] All v0.3.7 ecosystem checks successful.")

if __name__ == '__main__':
    run_tests()
