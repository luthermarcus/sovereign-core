#!/usr/bin/env python3
import json
import sqlite3
import sys
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode, HardwareWalletBridge

node = SovereignNode(is_regtest=True)

class APIServer(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self): self._set_headers(204)

    def do_GET(self):
        if self.path == '/api/metrics':
            with node.get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT balance FROM accounts WHERE address = 'genesis_faucet'")
                faucet = cur.fetchone()[0]
                cur.execute("SELECT balance FROM accounts WHERE address = 'depin_pool'")
                depin = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM depin_proofs")
                proofs = cur.fetchone()[0]

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "faucet_balance": faucet,
                "depin_pool_balance": depin,
                "verified_proofs": proofs,
                "edge_nodes": 142,
                "centralized_nodes": 18
            }).encode())

        elif self.path == '/api/bounties':
            with node.get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT bounty_id, title, target, funded FROM feature_bounties")
                rows = cur.fetchall()
            self._set_headers(200)
            self.wfile.write(json.dumps([{"id": r[0], "title": r[1], "target": r[2], "funded": r[3]} for r in rows]).encode())

        elif self.path == '/api/doctor':
            self._set_headers(200)
            self.wfile.write(json.dumps(node.doctor.run_diagnostics()).encode())
        else:
            self._set_headers(404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        if self.path == '/api/poc':
            self._set_headers(200)
            self.wfile.write(json.dumps(node.record_compute_proof(body.get("node_id", "local_edge_node"))).encode())

        elif self.path == '/api/split':
            try:
                res = node.process_5_5_90_split(
                    sender_addr=body.get("sender", "genesis_faucet"),
                    creator_addr=body.get("creator", "dev_app_creator"),
                    amount=float(body.get("amount", 100.0))
                )
                self._set_headers(200)
                self.wfile.write(json.dumps(res).encode())
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        elif self.path == '/api/bounties/pledge':
            b_id = body.get("bounty_id")
            amt = float(body.get("amount", 50.0))
            with node.get_conn() as conn:
                conn.execute("UPDATE feature_bounties SET funded = funded + ? WHERE bounty_id = ?", (amt, b_id))
                conn.commit()
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "pledged", "bounty_id": b_id, "amount": amt}).encode())

        elif self.path == '/api/psbt':
            self._set_headers(200)
            self.wfile.write(json.dumps(HardwareWalletBridge.generate_psbt(body.get("recipient", "bc1q..."), float(body.get("amount", 25.0)))).encode())

        elif self.path == '/api/prune':
            self._set_headers(200)
            self.wfile.write(json.dumps(node.prune_ledger(keep_days=int(body.get("keep_days", 7)))).encode())
        else:
            self._set_headers(404)

def run():
    server = HTTPServer(('127.0.0.1', 8545), APIServer)
    print("[DAEMON] Backend API listening on http://127.0.0.1:8545")
    server.serve_forever()

if __name__ == '__main__':
    run()
