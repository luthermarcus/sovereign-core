#!/usr/bin/env python3
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode, HardwareTelemetry

console = Console()
node = SovereignNode()

def render_wallet_control_center():
    telemetry = HardwareTelemetry.get_metrics()
    faucet_bal = node.get_balance("genesis_faucet")
    user_bal = node.get_balance("user_wallet_01")
    depin_bal = node.get_balance("depin_pool")
    
    with node.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM depin_proofs")
        proof_count = cur.fetchone()[0]

    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="bold white", justify="right")

    table.add_row("Node Profile", f"{node.config['node_profile']} ({telemetry['tier']})")
    table.add_row("CPU / RAM / Disk", f"{telemetry['cpu_pct']}% | {telemetry['ram_pct']}% RAM | {telemetry['disk_pct']}% Disk")
    table.add_row("--- Wallet Balances ---", "---")
    table.add_row("Genesis Faucet", f"{faucet_bal:,.2f} FOX")
    table.add_row("User Self-Custody", f"{user_bal:,.2f} FOX")
    table.add_row("DePIN Yield Pool", f"{depin_bal:,.2f} FOX")
    table.add_row("--- Ledger State ---", "---")
    table.add_row("Verified Proofs", str(proof_count))
    table.add_row("Micro-Batch Buffer", f"{len(node.batcher.buffer)} / {node.batcher.flush_threshold}")

    panel = Panel(
        table,
        title="[bold green]Sovereign Core v0.3.5 (Wallet & Node Terminal)[/bold green]",
        subtitle="[dim]Options: [1] Send Micro-Payment [2] Run Diagnostics [3] Exit[/dim]",
        border_style="green"
    )
    return panel

if __name__ == "__main__":
    console.clear()
    rprint("[green]>[/green] Booting Sovereign Core Wallet Terminal...")
    time.sleep(1)
    
    try:
        while True:
            console.clear()
            console.print(render_wallet_control_center())
            rprint("\n[bold cyan]Wallet Actions:[/bold cyan]")
            rprint("  [1] Send 5.0 FOX (Faucet -> User)")
            rprint("  [2] Run Node Diagnostics & Self-Healing")
            rprint("  [3] Refresh Telemetry View")
            rprint("  [4] Exit Terminal")
            
            choice = input("\nSelect action [1-4]: ").strip()
            if choice == "1":
                res = node.process_wallet_transfer("genesis_faucet", "user_wallet_01", 5.0)
                if res["status"] == "buffered":
                    rprint(f"[yellow]>[/yellow] Micro-payment buffered in memory. Buffer size: {res['buffer_size']}/3")
                else:
                    rprint(f"[green]✓[/green] Batch committed {res['count']} transfers to SQLite WAL ledger!")
                time.sleep(1.5)
            elif choice == "2":
                diag = node.run_diagnostics()
                rprint(f"[green]✓[/green] Diagnostics Status: [bold]{diag['status']}[/bold] ({diag['detail']})")
                time.sleep(2.0)
            elif choice == "4":
                rprint("[yellow]Shutting down Sovereign Wallet Terminal. Node running in background.[/yellow]")
                break
            else:
                time.sleep(0.5)
    except KeyboardInterrupt:
        rprint("\n[yellow]Terminal closed safely.[/yellow]")
