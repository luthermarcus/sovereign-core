import sqlite3
import os
import time

class SovereignPaymaster:
    """
    Acts as an ERC-4337 off-chain Paymaster. 
    Deducts a small ecosystem tax from DePIN node payouts (Mysterium, Honeygain, etc.)
    to fund a central gas treasury, allowing the ecosystem to sponsor its own transaction fees.
    """
    def __init__(self, db_path="/home/luther/node-stack/ecosystem_metrics.db"):
        self.db_path = db_path
        self.TAX_RATE_BPS = 150  # 1.5% tax to replenish the central gas pool
        self._init_db()

    def _init_db(self):
        # Connects to your existing ecosystem database
        os.makedirs(os.path.dirname(self.db_path) if '/' in self.db_path else '.', exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paymaster_treasury_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                node_app TEXT,
                payout_amount REAL,
                tax_collected REAL,
                gas_sponsored REAL,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def sponsor_withdrawal(self, node_app: str, payout_amount: float, estimated_gas_usd: float) -> tuple[bool, str, float]:
        # 1. Block transactions where the gas fee eats the entire payout (Economic Parasitism check)
        if estimated_gas_usd > (payout_amount * 0.15):
            self._log(node_app, payout_amount, 0, 0, "REJECTED_GAS_TOO_HIGH")
            return False, f"Gas fee (${estimated_gas_usd:.2f}) exceeds 15% of payout. Wait for lower network congestion.", payout_amount

        # 2. Calculate the ecosystem tax to fund future gas
        tax_collected = (payout_amount * self.TAX_RATE_BPS) / 10000
        net_to_wallet = payout_amount - tax_collected

        # 3. Log the successful sponsorship to the central treasury
        self._log(node_app, payout_amount, tax_collected, estimated_gas_usd, "SPONSORED_BY_ECOSYSTEM")
        return True, "Sponsorship Approved: Transaction fee routed through Sovereign Core treasury.", net_to_wallet

    def _log(self, node_app, payout, tax, gas, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO paymaster_treasury_log (timestamp, node_app, payout_amount, tax_collected, gas_sponsored, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (time.time(), node_app, payout, tax, gas, status))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    paymaster = SovereignPaymaster()
    
    # Test 1: Simulating a normal Mysterium payout
    status1, msg1, net1 = paymaster.sponsor_withdrawal("Mysterium Node", 14.25, 0.50)
    print(f"[{status1}] {msg1} | Final Wallet Deposit: ${net1:.2f}")

    # Test 2: Simulating a Honeygain payout during high Ethereum congestion
    status2, msg2, net2 = paymaster.sponsor_withdrawal("Honeygain", 11.40, 5.00)
    print(f"[{status2}] {msg2}")
