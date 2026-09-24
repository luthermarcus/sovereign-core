#!/usr/bin/env python3
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from sovereign_core import SovereignNode, HardwareTelemetry

def run_tests():
    print("--- Running Sovereign Core v0.3.5 Verification Suite ---")
    node = SovereignNode()
    
    # Verify Wallet Balance
    faucet_bal = node.get_balance("genesis_faucet")
    assert faucet_bal >= 0
    print(f"✓ Faucet balance verified: {faucet_bal} FOX")

    # Verify Transfer Execution
    res = node.process_wallet_transfer("genesis_faucet", "user_wallet_01", 10.0)
    assert res["status"] in ["buffered", "batch_committed"]
    print("✓ Wallet transfer & micro-batching verified")

    metrics = HardwareTelemetry.get_metrics()
    assert "tier" in metrics
    print(f"✓ Hardware telemetry verified ({metrics['tier']})")
    print("\n[PASSED] All v0.3.5 wallet and node checks successful.")

if __name__ == '__main__':
    run_tests()
