#!/usr/bin/env python3
import sys, argparse
sys.path.append(os.path.dirname(__file__))
from ccxt_adapter import query_ipc

parser = argparse.ArgumentParser(description="Sovereign SDK Command Line Tool")
parser.add_argument("--balance", action="store_true", help="Get local wallet balance")
parser.add_argument("--ticker", action="store_true", help="Get DEX orderbook ticker")

args = parser.parse_args()

if args.balance:
    res = query_ipc("get_balance")
    print(f"Balance: {res.get('balance')} FOX")
elif args.ticker:
    res = query_ipc("get_ticker")
    print(f"Market Ticker: {res}")
else:
    parser.print_help()
