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
        tbl.add_row("--- [bold yellow]📡 Security & Peer Stress Alerts[/bold yellow] ---", "---")
        tbl.add_row("System Integrity", "[bold green]● ALL WAL TABLES SECURE[/bold green]")
    else:
        for f in active_flags:
            col = "red" if f["level"] == "CRITICAL" else "yellow"
            tbl.add_row(f"FLAG: {f['key'][:12]}", f"[{col}]{f['message'][:22]}[/{col}]")

    st = state["storage"]
    tbl.add_row("--- [bold magenta]🔒 Secure Gateway & Stress Broadcast[/bold magenta] ---", "---")
    tbl.add_row("Peer Stress Notifications", f"[cyan]{state['stress_notified_peers']} Peers Notified of Load[/cyan]")
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
                rprint("  [1] 📥 Receive Funds (View Address & QR Data)")
                rprint("  [2] 💸 Send Transaction (Custom Fee Selection & Poison Guard)")
                rprint("  [3] 📢 Broadcast Stress Test Signal to Mesh Peers")
                rprint("  [4] ⚙️ Open Beta Options Manual (Toggle Feature Flags)")
                rprint("  [5] ➡️  Go to Menu Page 2 (Dev Tools & Simulation)")
                rprint("  [6] 🚪 Exit System")
                choice = input("\nSelect [1-6]: ").strip()
                
                if choice == "1":
                    console.clear()
                    rprint(Panel(f"[bold green]Receiving Dashboard[/bold green]\n\nYour Sovereign Address:\n[cyan]{state['wallet']['address']}[/cyan]\n\nBalances:\n• {state['wallet']['fox']} FOX\n• {state['wallet']['sats']} SATS", title="[Receive Menu]", border_style="cyan"))
                    input("\nPress [Enter] to return...")
                elif choice == "2":
                    console.clear()
                    rprint(Panel("[bold cyan]Protected Transfer Dashboard[/bold cyan]", title="[Send Menu]", border_style="cyan"))
                    recipient = input("Enter recipient address: ").strip()
                    if recipient:
                        try:
                            amount = float(input("Enter amount of FOX to send: ").strip())
                            res = node.send_transaction_with_fee(recipient, amount, 0.5)
                            rprint(f"\n[green]Transaction Result:[/green] {res}")
                        except ValueError:
                            rprint("[red]Invalid amount entered.[/red]")
                    input("\nPress [Enter] to return...")
                elif choice == "3":
                    console.clear()
                    res = node.broadcast_stress_signal_to_peers()
                    rprint(Panel(f"[bold cyan]Peer Stress Broadcast Result[/bold cyan]\n\n{res['message']}", title="[Stress Broadcast]", border_style="cyan"))
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    console.clear()
                    ff = state.get("feature_flags", {})
                    rprint(Panel(f"[bold yellow]Beta Options Manual[/bold yellow]\nConfigure experimental features.", title="[Options Manual]", border_style="yellow"))
                    rprint(f"  [1] Toggle Beta Telemetry ({ff.get('beta_telemetry_enabled')})")
                    rprint(f"  [2] Toggle P2P Auto-Update ({ff.get('p2p_auto_update_signaling')})")
                    rprint(f"  [3] Toggle Peer Stress Notifications ({ff.get('peer_stress_notifications')})")
                    opt = input("\nSelect flag to toggle [1-3] or press Enter: ").strip()
                    flag_map = {"1": "beta_telemetry_enabled", "2": "p2p_auto_update_signaling", "3": "peer_stress_notifications"}
                    if opt in flag_map:
                        res = node.toggle_feature_flag(flag_map[opt])
                        rprint(f"\n[green]Flag updated: {res}[/green]")
                        time.sleep(1)
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
                    plugins = node.get_loaded_plugins()
                    plug_summary = "\n".join([f"• [{p[0]}] {p[1]} ({p[2]}) - {p[3]}" for p in plugins])
                    rprint(Panel(f"[bold cyan]Plugins[/bold cyan]\n\n{plug_summary}", title="[Plugins]", border_style="yellow"))
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    console.clear()
                    txs = node.get_transaction_history() if hasattr(node, 'get_transaction_history') else []
                    tx_summary = "\n".join([f"• {t[0]} | {t[1]} {t[2]} FOX" for t in txs]) or "No transactions."
                    rprint(Panel(f"[bold cyan]Ledger[/bold cyan]\n\n{tx_summary}", title="[Ledger]", border_style="green"))
                    input("\nPress [Enter] to return...")
                elif choice == "5": page = 3
                elif choice == "6": page = 1
                    
            elif page == 3:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 3/3] ({ch}):[/bold cyan]")
                rprint("  [1] 🗺️ View Project Roadmap & Listing Milestones")
                rprint("  [2] 🔄 Toggle Release Channel (BETA ⇄ LIVE)")
                rprint("  [3] 💾 Backup Database (VACUUM INTO Snapshot)")
                rprint("  [4] ⬅️  Return to Menu Page 2")
                rprint("  [5] 🚪 Exit System")
                choice = input("\nSelect [1-5]: ").strip()
                
                if choice == "1":
                    console.clear()
                    rm = state.get("roadmap", {})
                    rprint(Panel(f"[bold]Phase:[/bold] {rm.get('current_phase')}\n[bold]Milestone:[/bold] {rm.get('next_milestone')}", title="Roadmap", border_style="cyan"))
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
                elif choice == "4": page = 2
                elif choice == "5": break
    except KeyboardInterrupt:
        pass
