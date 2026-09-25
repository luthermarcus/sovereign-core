#!/usr/bin/env python3
import sys, os, json, time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode, load_manifest

console = Console()
node = SovereignNode()
manifest = load_manifest()

def toggle_release_channel():
    current = manifest.get("release_channel", "BETA")
    manifest["release_channel"] = "LIVE" if current == "BETA" else "BETA"
    path = os.path.expanduser("~/sovereign-ecosystem/fork_manifest.json")
    with open(path, "w") as f: json.dump(manifest, f, indent=2)

def display_main_header():
    console.clear()
    state = node.query_full_status()
    flags = state["flags"]

    tbl = Table(show_header=False, box=None, expand=True)
    tbl.add_column("Key", style="cyan", ratio=1, no_wrap=True)
    tbl.add_column("Val", style="bold white", justify="right", ratio=1, no_wrap=True)

    active_flags = [f for f in flags if f["status"] == "ACTIVE"]
    if not active_flags:
        tbl.add_row("--- [bold yellow]📡 Security & Production Gateway[/bold yellow] ---", "---")
        tbl.add_row("System Integrity", "[bold green]● ALL WAL TABLES SECURE[/bold green]")
    else:
        for f in active_flags:
            col = "red" if f["level"] == "CRITICAL" else "yellow"
            tbl.add_row(f"FLAG: {f['key'][:12]}", f"[{col}]{f['message'][:22]}[/{col}]")

    st = state["storage"]
    ff = state.get("feature_flags", {})
    tbl.add_row("--- [bold magenta]🔑 Self-Custody & UTXO Coin Control[/bold magenta] ---", "---")
    tbl.add_row("Active UTXOs (Coin Control)", f"[cyan]{state['utxo_count']} Spendable Outputs[/cyan]")
    tbl.add_row("Sovereign Custody Mode", "[green]100% Client-Side Self-Owned[/green]")
    tbl.add_row("Blocked Connection Alerts", f"[red]{state['blocked_connections']} Endpoints Blocked[/red]")
    tbl.add_row("Local Storage Allocation", f"{st['used_mb']:.1f} MB / {st['cap_mb']} MB (Cap Guard)")
    tbl.add_row("--- [bold green]₿ AMM DEX & Balances[/bold green] ---", "---")
    tbl.add_row("FOX / SATS Reserve", f"{state['reserves']['fox']:,.0f} │ {state['reserves']['sats']:,.0f}")
    tbl.add_row("Local User Wallet", f"{state['wallet']['fox']:.1f} FOX │ {state['wallet']['sats']:,.0f} SATS")

    console.print(Panel(tbl, title=f"[bold green]Sovereign Ecosystem {state['version']} [{state['release_channel']} CHANNEL][/bold green]", border_style="green"))

if __name__ == "__main__":
    try:
        page = 1
        while True:
            display_main_header()
            state = node.query_full_status()
            ch = state["release_channel"]
            
            if page == 1:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 1/3] ({ch}):[/bold cyan]")
                rprint("  [1] 📥 Receive Funds & View Address")
                rprint("  [2] 💸 Send Transaction (Dynamic Fee Selection)")
                rprint("  [3] 🪙 View UTXO Ledger & Coin Control Details")
                rprint("  [4] ℹ️  Interactive Guidance Manual & Ecosystem Help Flags")
                rprint("  [5] ➡️  Go to Menu Page 2 (Dev Tools & Bridges)")
                rprint("  [6] 🚪 Exit System")
                choice = input("\nSelect [1-6]: ").strip()
                
                if choice == "1":
                    console.clear()
                    rprint(Panel(f"[bold green]Receiving Dashboard[/bold green]\n\nYour Self-Owned Address:\n[cyan]{state['wallet']['address']}[/cyan]\n\n[yellow]Tip: Always verify your address on a secure offline device before receiving funds.[/yellow]", title="[Receive Guidance]", border_style="cyan"))
                    input("\nPress [Enter] to return...")
                elif choice == "2":
                    console.clear()
                    rprint(Panel("[bold cyan]Protected Transfer Dashboard[/bold cyan]\n[yellow]Guidance: Fees adjust dynamically based on network priority (Low / Med / High).[/yellow]", title="[Send Menu]", border_style="cyan"))
                    recipient = input("Enter recipient address: ").strip()
                    if recipient:
                        try:
                            amount = float(input("Enter amount of FOX to send: ").strip())
                            print("Select Fee Rate Priority:\n [1] Low (0.2 FOX)\n [2] Normal (0.5 FOX)\n [3] High (1.0 FOX)")
                            fee_choice = input("Select fee [1-3]: ").strip()
                            fee_rate = 0.2 if fee_choice == "1" else (1.0 if fee_choice == "3" else 0.5)
                            res = node.send_transaction_with_fee(recipient, amount, fee_rate)
                            rprint(f"\n[green]Transaction Result:[/green] {res}")
                        except ValueError:
                            rprint("[red]Invalid input entered.[/red]")
                    input("\nPress [Enter] to return...")
                elif choice == "3":
                    console.clear()
                    utxos = node.get_utxo_list()
                    utxo_summary = "\n".join([f"• ID: {u[0]} │ Amount: {u[1]} FOX │ TXID: {u[2]}" for u in utxos]) or "No unspent UTXOs found."
                    rprint(Panel(f"[bold cyan]UTXO Ledger & Coin Control[/bold cyan]\n\n{utxo_summary}\n\n[yellow]Guidance: Managing UTXOs allows you to control which inputs are spent to save on transaction fees.[/yellow]", title="[UTXO Details]", border_style="cyan"))
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    console.clear()
                    rprint(Panel(f"[bold yellow]Interactive Ecosystem Guidance Manual[/bold yellow]\n\n• [cyan]Page 1, Option 1:[/cyan] View your self-owned cryptographic address.\n• [cyan]Page 1, Option 2:[/cyan] Send FOX with custom fee priority rates.\n• [cyan]Page 1, Option 3:[/cyan] Inspect unspent outputs (UTXOs) for coin control.\n• [cyan]Page 2, Option 1-4:[/cyan] Execute cross-chain swaps, SQL queries, and plugins.\n• [cyan]Page 3, Option 2:[/cyan] Toggle release channels (BETA auto-prunes in LIVE).\n\n[green]All systems operate locally with zero server custody.[/green]", title="[Help & Guidance Flags]", border_style="yellow"))
                    input("\nPress [Enter] to return...")
                elif choice == "5": page = 2
                elif choice == "6": break
                    
            elif page == 2:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 2/3] ({ch}):[/bold cyan]")
                rprint("  [1] 🌉 Initiate HTLC Cross-Chain Bridge Swap")
                rprint("  [2] 🛠️ Developer SQL Sandbox & Query Shell")
                rprint("  [3] 🔌 Manage Local Plugins & Module Registry")
                rprint("  [4] 📜 View Transaction History Ledger Dashboard")
                rprint("  [5] ➡️  Go to Menu Page 3")
                rprint("  [6] ⬅️  Return to Menu Page 1")
                choice = input("\nSelect [1-6]: ").strip()
                
                if choice == "1":
                    console.clear()
                    rprint(Panel("[bold cyan]HTLC Bridge Dashboard[/bold cyan]", title="[Bridge Menu]", border_style="cyan"))
                    target = input("Destination chain: ").strip() or "EVM-L2"
                    try:
                        amt = float(input("Amount to lock: ").strip() or "10")
                        res = node.initiate_htlc_bridge(amt, target)
                        rprint(f"\n[green]Bridge Locked:[/green] {res}")
                    except ValueError: rprint("[red]Invalid input.[/red]")
                    input("\nPress [Enter] to return...")
                elif choice == "2":
                    console.clear()
                    rprint(Panel("[bold cyan]SQL Sandbox Shell[/bold cyan]", title="[SQL Shell]", border_style="yellow"))
                    sql_query = input("Enter SQL Query: ").strip()
                    if sql_query:
                        res = node.execute_custom_sql(sql_query)
                        rprint(f"\n[green]Result:[/green] {res}")
                    input("\nPress [Enter] to return...")
                elif choice == "3":
                    console.clear()
                    rprint(Panel("[bold cyan]Plugins Loaded[/bold cyan]", title="[Plugins]", border_style="yellow"))
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    console.clear()
                    rprint(Panel("[bold cyan]Transaction Ledger History[/bold cyan]", title="[Ledger]", border_style="green"))
                    input("\nPress [Enter] to return...")
                elif choice == "5": page = 3
                elif choice == "6": page = 1
                    
            elif page == 3:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 3/3] ({ch}):[/bold cyan]")
                rprint("  [1] 🗺️ View Project Roadmap & Listing Milestones")
                rprint("  [2] 🔄 Toggle Release Channel (BETA ⇄ LIVE)")
                rprint("  [3] 💾 Backup Database (VACUUM INTO Snapshot)")
                rprint("  [4] 🔑 View Self-Custody Sovereign Seed & Key Backup")
                rprint("  [5] ⬅️  Return to Menu Page 2")
                rprint("  [6] 🚪 Exit System")
                choice = input("\nSelect [1-6]: ").strip()
                
                if choice == "1":
                    console.clear()
                    rprint(Panel("[bold]Current Phase:[/bold] Phase XXXIII: Production Hardening & Pre-Checks", title="Roadmap", border_style="cyan"))
                    input("\nPress [Enter] to return...")
                elif choice == "2":
                    toggle_release_channel()
                    manifest = load_manifest()
                    node.config = manifest
                    rprint(f"\n[green]Channel switched to: {manifest.get('release_channel')}[/green]")
                    time.sleep(1.5)
                elif choice == "3":
                    console.clear()
                    res = node.create_live_backup()
                    rprint(Panel(f"[bold cyan]Backup Result[/bold cyan]\n\n{res}", title="[Backup]", border_style="green"))
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    console.clear()
                    vault_data = node.key_vault.get_user_vault_details()
                    rprint(Panel(f"[bold cyan]Self-Custody Sovereign Key Vault[/bold cyan]\n\nAddress: [cyan]{vault_data.get('owner_sovereign_address')}[/cyan]\nSeed Entropy: [yellow]{vault_data.get('client_seed_entropy')}[/yellow]\n\n[red]{vault_data.get('warning')}[/red]", title="[Key Backup]", border_style="cyan"))
                    input("\nPress [Enter] to return...")
                elif choice == "5": page = 2
                elif choice == "6": break
    except KeyboardInterrupt:
        pass
