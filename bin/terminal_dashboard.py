#!/usr/bin/env python3
import sys, os, time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode, HardwareTelemetry

console = Console()
node = SovereignNode()

def display_dashboard():
    console.clear()
    t = HardwareTelemetry.get_metrics()
    user_fox = node.get_balance("user_wallet_01")
    user_sats = node.get_balance("user_wallet_01_sats")
    depin = node.get_balance("depin_pool")
    res_a, res_b, lp = node.get_pool_info()
    with node.get_conn() as conn:
        proofs = conn.cursor().execute("SELECT COUNT(*) FROM depin_proofs").fetchone()[0]

    tbl = Table(show_header=False, box=None, expand=True)
    tbl.add_column("Key", style="cyan")
    tbl.add_column("Val", style="bold white", justify="right")
    
    tbl.add_row("--- Core Node & Security ---", "---")
    tbl.add_row("Node Profile", f"{node.config['node_profile']} ({t['tier']})")
    tbl.add_row("Security Status", "[green]AES-256-CBC (WAL Active)[/green]")
    tbl.add_row("Privacy Mode", f"[yellow]{node.config['privacy_mode'].upper()}[/yellow]")
    tbl.add_row("CPU / RAM / Disk", f"{t['cpu_pct']}% | {t['ram_pct']}% RAM | {t['disk_pct']}% Disk")
    
    tbl.add_row("--- DePIN & Mining Channel ---", "---")
    tbl.add_row("DePIN Yield Pool", f"{depin:,.2f} FOX | Proofs: {proofs}")
    
    tbl.add_row("--- DEX AMM Liquidity Channel ---", "---")
    tbl.add_row("FOX / SATS Reserve", f"{res_a:,.2f} / {res_b:,.2f}")
    
    tbl.add_row("--- Wallet & Dev Channel ---", "---")
    tbl.add_row("User FOX / SATS", f"{user_fox:,.2f} / {user_sats:,.2f}")
    tbl.add_row("Prompt Assistant Mode", "[cyan]Ready (Type '/' for commands)[/cyan]")

    console.print(Panel(tbl, title="[bold green]Sovereign Core v0.5.3 Interactive Control Center[/bold green]", border_style="green"))

if __name__ == "__main__":
    try:
        while True:
            display_dashboard()
            rprint("\n[bold cyan]Developer & Node Channels:[/bold cyan]")
            rprint("  [1] ⛏️  Trigger DePIN Mining Round")
            rprint("  [2] 💱 Swap 10 FOX -> SATS (AMM DEX)")
            rprint("  [3] 💱 Swap 1000 SATS -> FOX (AMM DEX)")
            rprint("  [4] 🔒 Toggle Privacy Mode (Local vs Federated)")
            rprint("  [5] 🛠️  Run Diagnostics & Security Audit")
            rprint("  [6] 💬 Open Prompt Assistant (Command Palette)")
            rprint("  [7] 🚪 Exit Control Center")
            
            try:
                choice = input("\nEnter option [1-7] or command: ").strip()
            except (KeyboardInterrupt, EOFError):
                rprint("\n[yellow]Shutdown signal received.[/yellow]")
                break

            # Handle Prompt Assistant / Natural Commands starting with '/'
            if choice.startswith("/"):
                parts = choice.split()
                cmd = parts[0].lower()
                if cmd == "/help":
                    rprint("\n[cyan]Available Prompt Assistant Commands:[/cyan]")
                    rprint("  /mine          - Execute DePIN PoC mining")
                    rprint("  /swap <amount> - Swap FOX to SATS")
                    rprint("  /balance       - Check wallet balances")
                    rprint("  /audit         - Run security diagnostics")
                elif cmd == "/mine":
                    res = node.mine_depin_proof()
                    rprint(f"\n[green]✓[/green] Mined successfully! Reward: +{res.get('reward', 0)} FOX")
                elif cmd == "/swap":
                    amt = float(parts[1]) if len(parts) > 1 else 10.0
                    res = node.execute_amm_swap(amt, True)
                    rprint(f"\n[green]✓[/green] Swapped {amt} FOX for [bold]{res['amount_out']:.2f} SATS[/bold]")
                elif cmd == "/balance":
                    rprint(f"\n[green]✓[/green] FOX: {node.get_balance('user_wallet_01')} | SATS: {node.get_balance('user_wallet_01_sats')}")
                elif cmd == "/audit":
                    diag = node.run_diagnostics()
                    rprint(f"\n[green]✓[/green] {diag['status']}: {diag['detail']}")
                else:
                    rprint(f"\n[red]Unknown command '{cmd}'. Type /help for assistance.[/red]")
                input("\nPress [Enter] to continue...")
                continue

            if choice == "1":
                rprint("\n[yellow]>[/yellow] Mining DePIN proof...")
                res = node.mine_depin_proof()
                rprint(f"[green]✓[/green] Mined successfully! Reward: +{res.get('reward', 0)} FOX")
            elif choice == "2":
                res = node.execute_amm_swap(10.0, True)
                rprint(f"\n[green]✓[/green] Swapped 10 FOX for [bold]{res['amount_out']:.2f} SATS[/bold]")
            elif choice == "3":
                res = node.execute_amm_swap(1000.0, False)
                rprint(f"\n[green]✓[/green] Swapped 1000 SATS for [bold]{res['amount_out']:.2f} FOX[/bold]")
            elif choice == "4":
                mode = "federated_p2p" if node.config["privacy_mode"] == "local_only" else "local_only"
                node.set_privacy_mode(mode)
                rprint(f"\n[green]✓[/green] Privacy mode updated to: [bold cyan]{mode.upper()}[/bold cyan]")
            elif choice == "5":
                diag = node.run_diagnostics()
                rprint(f"\n[green]✓[/green] {diag['status']}: {diag['detail']}")
            elif choice == "6":
                rprint("\n[cyan]💬 Prompt Assistant Mode Activated![/cyan]")
                rprint("Type commands like [bold]/mine[/bold], [bold]/swap 50[/bold], [bold]/balance[/bold], or [bold]/help[/bold]:")
                p_cmd = input("prompt> ").strip()
                if p_cmd.startswith("/help"):
                    rprint("Commands: /mine, /swap <amt>, /balance, /audit")
                elif p_cmd.startswith("/mine"):
                    res = node.mine_depin_proof()
                    rprint(f"[green]✓[/green] Mined! Reward: +{res.get('reward', 0)} FOX")
                elif p_cmd.startswith("/swap"):
                    amt = float(p_cmd.split()[1]) if len(p_cmd.split()) > 1 else 10.0
                    res = node.execute_amm_swap(amt, True)
                    rprint(f"[green]✓[/green] Swapped {amt} FOX for {res['amount_out']:.2f} SATS")
                elif p_cmd.startswith("/balance"):
                    rprint(f"[green]✓[/green] FOX: {node.get_balance('user_wallet_01')} | SATS: {node.get_balance('user_wallet_01_sats')}")
                elif p_cmd.startswith("/audit"):
                    diag = node.run_diagnostics()
                    rprint(f"[green]✓[/green] {diag['status']}: {diag['detail']}")
                else:
                    rprint("[red]Unknown command.[/red]")
            elif choice == "7":
                rprint("\n[yellow]Exiting control center safely.[/yellow]")
                break
            else:
                rprint("\n[red]Invalid option. Please choose between 1 and 7.[/red]")
            
            input("\nPress [Enter] to continue...")
    except KeyboardInterrupt:
        rprint("\n[yellow]Control center closed via interrupt.[/yellow]")
