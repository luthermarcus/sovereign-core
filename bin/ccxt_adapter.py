#!/usr/bin/env python3
import json, socket, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.append(os.path.dirname(__file__))
from sovereign_core import load_manifest

config = load_manifest()
IPC_PORT = config.get("ipc_tcp_port", 8332)

def query_ipc(method, params=None):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', IPC_PORT))
        req = json.dumps({"jsonrpc": "2.0", "method": method, "params": params or {}})
        sock.sendall(req.encode('utf-8'))
        resp = json.loads(sock.recv(4096).decode('utf-8'))
        sock.close()
        return resp.get("result", {})
    except Exception as e:
        return {"error": str(e)}

class CCXTExchangeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        if self.path == '/api/v1/ticker':
            self.wfile.write(json.dumps({"success": True, "ticker": query_ipc("get_ticker")}).encode())
        elif self.path == '/api/v1/balance':
            self.wfile.write(json.dumps({"success": True, "balance": query_ipc("get_balance")}).encode())
        else:
            self.wfile.write(json.dumps({"error": "Endpoint not supported"}).encode())

    def log_message(self, format, *args): pass

# FIX: Allow reuse address prevents Errno 98 on restart
class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    port = config.get("ccxt_rest_port", 8080)
    server = ReusableHTTPServer(('127.0.0.1', port), CCXTExchangeHandler)
    server.serve_forever()
