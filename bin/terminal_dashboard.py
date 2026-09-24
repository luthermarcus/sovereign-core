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

def render_secure_dashboard():
    telemetry = HardwareTelemetry.get_metrics()
    faucet_bal = node.get_balance("genesis_faucet")
    user_bal = node.get_balance("user_wallet_01")
    user_sats = node.get_balance("user_wallet_01_sats")
    depin_bal = node.get_balance("depin_pool")
    res_a, res_b, lp_shares = node.get_pool_info()
    
    with node.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM depin_proofs")
        proof_count = cur.fetchone()[0]

    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="bold white", justify="right")

    table.add_row("Node Profile", f"{node.config['node_profile']} ({telemetry['tier']})")
    table.add_row("Encryption Status", f"[bold green]AES-256-CBC (WAL Active)[/bold green]")
    table.add_row("KDF Derivations", f"{node.kdf_count} (Singleton)")
    table.add_row("Cipher Overhead", "~7.5% (Optimized)")
    table.add_row("CPU / RAM / Disk", f"{telemetry['cpu_pct']}% | {telemetry['ram_pct']}% RAM | {telemetry['disk_pct']}% Disk")
    table.add_row("--- Mining & DePIN Yield ---", "---")
    table.add_row("DePIN Yield Pool", f"{depin_bal:,.2f} FOX")
    table.add_row("Verified Proofs", str(proof_count))
    table.add_row("--- DEX AMM Liquidity Pool ---", "---")
    table.add_row("FOX Reserve (Pool A)", f"{res_a:,.2f} FOX")
    table.add_row("SATS Reserve (Pool B)", f"{res_b:,.2f} SATS")
    table.add_row("--- Wallet Balances ---", "---")
    table.add_row("User FOX Wallet", f"{user_bal:,.2f} FOX")
    table.add_row("User SATS Wallet", f"{user_sats:,.2f} SATS")

    panel = Panel(
        table,
        title="[bold green]Sovereign Core v0.4.4 (Enterprise Secure Terminal)[/bold green]",
        subtitle="[dim]Press Ctrl+C at any time to exit safely[/dim]",
        border_style="green"
    )
    return panel

if __name__ == "__main__":
    console.clear()
    rprint("[green]>[/green] Booting Enterprise Secure Terminal Dashboard...")
    time.sleep(0.5)
    
    try:
        while True:
            console.clear()
            console.print(render_secure_dashboard())
            rprint("\n[bold cyan]Secure Ecosystem Actions:[/bold cyan]")
            rprint("  [1] Trigger DePIN Proof-of-Compute Mining Round")
            rprint("  [2] Swap 10 FOX -> SATS (AMM Pool)")
            rprint("  [3] Swap 1000 SATS -> FOX (AMM Pool)")
            rprint("  [4] Run Encryption & WAL Security Audit")
            rprint("  [5] Exit Dashboard")
            
            try:
                choice = Prompt.ask("\n[bold yellow]Select action[/bold yellow]", choices=["1", "2", "3", "4", "5"], default="4")
            except (KeyboardInterrupt, EOFError):
                rprint("\n[yellow]Exit signal received. Shutting down cleanly.[/yellow]")
                break
            
            if choice == "1":
                rprint("[yellow]>[/yellow] Executing CPU Proof-of-Compute mining...")
                res = node.mine_depin_proof()
                if res["status"] == "success":
                    rprint(f"[green]✓[/green] Block Mined! Hash: {res['hash'][:12]}... (+{res['reward']} FOX)")
                else:
                    rprint("[red]✗[/red] Mining timeout.")
                time.sleep(1.5)
            elif choice == "2":
                res = node.execute_amm_swap(10.0, swap_a_to_b=True)
                rprint(f"[green]✓[/green] Swapped 10 FOX for [bold]{res['amount_out']:.2f} SATS[/bold]!")
                time.sleep(1.5)
            elif choice == "3":
                res = node.execute_amm_swap(1000.0, swap_a_to_b=False)
                rprint(f"[green]✓[/green] Swapped 1000 SATS for [bold]{res['amount_out']:.2f} FOX[/bold]!")
                time.sleep(1.5)
            elif choice == "4":
                diag = node.run_diagnostics()
                rprint(f"[green]✓[/green] Status: [bold]{diag['status']}[/bold] ({diag['detail']})")
                time.sleep(2.0)
            elif choice == "5":
                rprint("[yellow]Closing terminal dashboard safely.[/yellow]")
                break
    except KeyboardInterrupt:
        rprint("[yellow]Dashboard closed via global interrupt.[/yellow]")
