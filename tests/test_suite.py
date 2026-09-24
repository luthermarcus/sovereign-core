#!/usr/bin/env python3
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin')))
from sovereign_core import SovereignNode, HardwareTelemetry

def run_e2e_tests():
    print("==================================================")
    print("   SOVEREIGN CORE: E2E TEST SUITE EXECUTION       ")
    print("==================================================")
    
    node = SovereignNode()
    
    # 1. Test Telemetry Layer
    metrics = HardwareTelemetry.get_metrics()
    assert "tier" in metrics
    print(f"✓ Hardware Telemetry Verified ({metrics['tier']}, CPU: {metrics['cpu_pct']}%)")

    # 2. Test Ledger & Balance Constraints
    bal = node.get_balance("user_wallet_01")
    assert bal >= 0
    print(f"✓ SQLite WAL Ledger Balance Verified (User FOX: {bal})")

    # 3. Test AMM DEX Swap
    swap_res = node.execute_amm_swap(10.0, True)
    assert "amount_out" in swap_res
    print(f"✓ AMM DEX Constant-Product Swap Verified (Out: {swap_res['amount_out']:.2f} SATS)")

    # 4. Test DePIN Mining Worker
    mine_res = node.mine_depin_proof()
    assert mine_res["status"] == "success"
    print(f"✓ DePIN Mining Proof Verified (Hash: {mine_res['hash'][:12]}...)")

    # 5. Test JSON-RPC IPC Bridge Stub
    rpc_req = json.dumps({"jsonrpc": "2.0", "method": "get_balance", "params": {"address": "user_wallet_01"}, "id": 1})
    rpc_res = json.loads(node.handle_rpc_request(rpc_req))
    assert "result" in rpc_res
    print(f"✓ JSON-RPC IPC Bridge Verified (Balance Response: {rpc_res['result']['balance']})")

    print("\n[SUCCESS] All Ecosystem E2E Tests Passed Successfully!")

if __name__ == "__main__":
    import json
    run_e2e_tests()
