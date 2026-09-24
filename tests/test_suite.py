#!/usr/bin/env python3
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from sovereign_core import SovereignNode, HardwareTelemetry

def run_tests():
    print("--- Running Sovereign Core v0.3.0 Verification ---")
    node = SovereignNode(is_regtest=True)
    metrics = HardwareTelemetry.get_metrics()
    assert "tier" in metrics
    print(f"✓ Hardware Telemetry verified ({metrics['tier']})")
    
    diag = node.run_diagnostics()
    assert diag["status"] == "OPTIMAL"
    print("✓ SQLite WAL & Node Diagnostics verified")
    print("\n[PASSED] All checks successful.")

if __name__ == '__main__':
    run_tests()
