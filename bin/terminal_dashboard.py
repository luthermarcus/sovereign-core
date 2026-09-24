#!/usr/bin/env python3
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich import print as rprint

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode, HardwareTelemetry

console = Console()
node = SovereignNode(is_regtest=True)

def render_dashboard():
    telemetry = HardwareTelemetry.get_metrics()
    
    with node.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM accounts WHERE address = 'genesis_faucet'")
        faucet_bal = cur.fetchone()[0]
        cur.execute("SELECT balance FROM accounts WHERE address = 'depin_pool'")
        depin_bal = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM depin_proofs")
        proof_count = cur.fetchone()[0]

    # Main Layout Construction
    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold white", justify="right")

    table.add_row("Node Tier", telemetry['tier'])
    table.add_row("CPU Load", f"{telemetry['cpu_pct']}%")
    table.add_row("RAM Usage", f"{telemetry['ram_used']:.2f} GB / {telemetry['ram_total']:.2f} GB ({telemetry['ram_pct']}%)")
    table.add_row("Disk Free", f"{telemetry['disk_free']:.2f} GB / {telemetry['disk_total']:.2f} GB ({telemetry['disk_pct']}% used)")
    table.add_row("--- WAL Ledger ---", "---")
    table.add_row("Faucet Reserve", f"{faucet_bal:,.2f} FOX")
    table.add_row("DePIN Yield Pool", f"{depin_bal:,.2f} FOX")
    table.add_row("Verified Proofs", str(proof_count))
    table.add_row("Buffer Queue", f"{len(node.batcher.buffer)} / {node.batcher.flush_threshold}")

    panel = Panel(
        table,
        title="[bold green]Sovereign Core v0.3.0-beta (Live Telemetry)[/bold green]",
        subtitle="[dim]Press Ctrl+C to exit dashboard[/dim]",
        border_style="green"
    )
    return panel

if __name__ == "__main__":
    console.clear()
    rprint("[green]>[/green] Launching Sovereign Core Live Telemetry Dashboard...")
    try:
        while True:
            console.clear()
            console.print(render_dashboard())
            time.sleep(2.0)
    except KeyboardInterrupt:
        rprint("\n[yellow]Dashboard closed. Node running in background.[/yellow]")
