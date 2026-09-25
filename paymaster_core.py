import sqlite3
import os
import time

class SovereignPaymaster:
    def __init__(self, db_path="/home/luther/node-stack/ecosystem_metrics.db"):
        self.db_path = db_path
        self.TAX_RATE_BPS = 150
        self.MAX_FEE_RATIO = 0.15
        self._init_db()

    def _init_db(self):
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

    def get_pool_balance(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT SUM(tax_collected), SUM(gas_sponsored) FROM paymaster_treasury_log")
            row = cursor.fetchone()
            balance = (row[0] or 0.0) - (row[1] or 0.0)
        except:
            balance = 0.0
        conn.close()
        return balance

    def sponsor_withdrawal(self, node_app: str, payout_amount: float, estimated_gas_usd: float) -> tuple[bool, str, float]:
        if payout_amount <= 0:
            return False, "Payout amount must be greater than zero.", 0.0
        if estimated_gas_usd > (payout_amount * self.MAX_FEE_RATIO):
            self._log(node_app, payout_amount, 0, 0, "REJECTED_PARASITIC_FEE")
            return False, f"Gas fee (${estimated_gas_usd:.2f}) exceeds 15% threshold.", payout_amount
        
        current_pool = self.get_pool_balance()
        tax_collected = (payout_amount * self.TAX_RATE_BPS) / 10000
        
        # FIX: ERC-4337 Deposit Requirement Safeguard
        if estimated_gas_usd > (current_pool + tax_collected):
            self._log(node_app, payout_amount, 0, 0, "REJECTED_TREASURY_DEFICIT")
            return False, f"Insufficient Treasury: Gas (${estimated_gas_usd:.2f}) exceeds pool.", payout_amount

        net_deposit = payout_amount - tax_collected
        self._log(node_app, payout_amount, tax_collected, estimated_gas_usd, "SPONSORED_SUCCESS")
        return True, "Approved: Subsidized by sovereign treasury pool.", net_deposit

    def _log(self, node_app, payout, tax, gas, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO paymaster_treasury_log (timestamp, node_app, payout_amount, tax_collected, gas_sponsored, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (time.time(), node_app, payout, tax, gas, status))
        conn.commit()
        conn.close()
