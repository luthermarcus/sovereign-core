#!/usr/bin/env python3
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import print as rprint

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode, HardwareTelemetry

console = Console()
node = SovereignNode()

def render_privacy_dashboard():
    telemetry = HardwareTelemetry.get_metrics()
    faucet_bal = node.get_balance("genesis_faucet")
    user_bal = node.get_balance("user_wallet_01")
    
    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="bold white", justify="right")

    table.add_row("Node Profile", f"{node.config['node_profile']} ({telemetry['tier']})")
    table.add_row("Privacy Posture", f"[bold yellow]{node.config['privacy_mode'].upper()}[/bold yellow]")
    table.add_row("CPU / RAM / Disk", f"{telemetry['cpu_pct']}% | {telemetry['ram_pct']}% RAM | {telemetry['disk_pct']}% Disk")
    table.add_row("--- Wallet Balances ---", "---")
    table.add_row("Genesis Faucet", f"{faucet_bal:,.2f} FOX")
    table.add_row("User Self-Custody", f"{user_bal:,.2f} FOX")

    panel = Panel(
        table,
        title="[bold green]Sovereign Core v0.4.1 (Privacy-Enabled Terminal)[/bold green]",
        subtitle="[dim]Press Ctrl+C at any time to exit safely[/dim]",
        border_style="green"
    )
    return panel

if __name__ == "__main__":
    console.clear()
    rprint("[green]>[/green] Booting Privacy-Enabled Terminal Dashboard...")
    time.sleep(0.5)
    
    try:
        while True:
            console.clear()
            console.print(render_privacy_dashboard())
            rprint("\n[bold cyan]Privacy & Wallet Actions:[/bold cyan]")
            rprint("  [1] Toggle Privacy Mode (Local-Only vs. Federated P2P)")
            rprint("  [2] Run Node Diagnostics & Privacy Audit")
            rprint("  [3] Refresh Telemetry View")
            rprint("  [4] Exit Dashboard")
            
            try:
                choice = Prompt.ask("\n[bold yellow]Select action[/bold yellow]", choices=["1", "2", "3", "4"], default="3")
            except (KeyboardInterrupt, EOFError):
                rprint("\n[yellow]Exit signal received. Shutting down cleanly.[/yellow]")
                break
            
            if choice == "1":
                current = node.config["privacy_mode"]
                new_mode = "federated_p2p" if current == "local_only" else "local_only"
                node.set_privacy_mode(new_mode)
                rprint(f"[green]✓[/green] Privacy mode updated to: [bold cyan]{new_mode.upper()}[/bold cyan]")
                time.sleep(1.5)
            elif choice == "2":
                diag = node.run_diagnostics()
                rprint(f"[green]✓[/green] Status: [bold]{diag['status']}[/bold] ({diag['detail']})")
                time.sleep(2.0)
            elif choice == "4":
                rprint("[yellow]Closing terminal dashboard safely.[/yellow]")
                break
    except KeyboardInterrupt:
        rprint("\n[yellow]Dashboard closed via global interrupt.[/yellow]")
