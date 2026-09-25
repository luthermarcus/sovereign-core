#!/usr/bin/env python3
import sys, os, argparse, json
sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode

parser = argparse.ArgumentParser(description="Sovereign Developer Toolkit & Query Engine")
parser.add_argument("--status", action="store_true", help="Dump entire node state as JSON")
parser.add_argument("--flags", action="store_true", help="Query all system integrity flags")
parser.add_argument("--swap", type=float, help="Execute protected AMM swap with exact FOX input")
parser.add_argument("--sandbox", action="store_true", help="Dump developer telemetry logs for forensic debugging")

args = parser.parse_args()
node = SovereignNode()
node.run_internal_health_queries()
node.check_wallet_alerts()

if args.status:
    print(json.dumps(node.query_full_status(), indent=2))
elif args.flags:
    print(json.dumps(node.query_system_flags(), indent=2))
elif args.sandbox:
    print(json.dumps(node.query_dev_sandbox(), indent=2))
elif args.swap is not None:
    print(json.dumps(node.execute_protected_swap_query(args.swap), indent=2))
else:
    parser.print_help()
