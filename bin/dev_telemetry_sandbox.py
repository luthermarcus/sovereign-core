#!/usr/bin/env python3
import sys, os, time
from rich.console import Console
from rich.table import Table
sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode

console = Console()
node = SovereignNode()

def run_tracker():
    console.print("\n[bold yellow]🧪 SOVEREIGN DEV TELEMETRY SANDBOX[/bold yellow]")
    console.print("This standalone script tracks internal node execution. Delete before Mainnet.\n")
    
    with node.get_conn() as conn:
        logs = conn.execute("SELECT timestamp, event_type, payload FROM dev_telemetry_logs ORDER BY timestamp DESC LIMIT 5").fetchall()
    
    tbl = Table(show_header=True, header_style="bold magenta")
    tbl.add_column("Time (Epoch)")
    tbl.add_column("Event Type")
    tbl.add_column("Payload")
    
    for l in logs:
        tbl.add_row(f"{l[0]:.2f}", l[1], l[2])
    
    console.print(tbl)
    print("\n[Sandbox complete. Returning to node...]")

if __name__ == "__main__":
    run_tracker()
