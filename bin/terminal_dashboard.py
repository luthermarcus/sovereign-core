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
    manifest["release_channel"] = "DEV" if current == "BETA" else "BETA"
    path = os.path.expanduser("~/sovereign-ecosystem/fork_manifest.json")
    with open(path, "w") as f: json.dump(manifest, f, indent=2)

def display_view():
    console.clear()
    state = node.query_full_status()
    flags = state["flags"]

    tbl = Table(show_header=False, box=None, expand=True)
    tbl.add_column("Channel", style="cyan", ratio=1, no_wrap=True)
    tbl.add_column("State", style="bold white", justify="right", ratio=1, no_wrap=True)

    active_flags = [f for f in flags if f["status"] == "ACTIVE"]
    if not active_flags:
        tbl.add_row("--- [bold yellow]📡 Security & Flags[/bold yellow] ---", "---")
        tbl.add_row("System Integrity", "[bold green]● ALL FLAGS GREEN[/bold green]")
    else:
        for f in active_flags:
            tbl.add_row(f"FLAG: {f['key'][:12]}", f"[yellow]{f['message'][:22]}[/yellow]")

    tbl.add_row("--- [bold magenta]🎵 Web3 Media & Bridge[/bold magenta] ---", "---")
    tbl.add_row("Cached Audio Tracks", f"{state['media_downloaded']} Downloaded (IPFS)")
    tbl.add_row("Active HTLC Locks", f"{state['bridge_locked']} Cross-Chain Swaps")
    tbl.add_row("--- [bold green]₿ AMM DEX & Balances[/bold green] ---", "---")
    tbl.add_row("FOX / SATS Reserve", f"{state['reserves']['fox']:,.0f} │ {state['reserves']['sats']:,.0f}")
    tbl.add_row("Local User Wallet", f"{state['wallet']['fox']:.1f} FOX │ {state['wallet']['sats']:,.0f} SATS")

    console.print(Panel(tbl, title=f"[bold green]Sovereign Ecosystem {state['version']} [{state['release_channel']} CHANNEL][/bold green]", border_style="green"))

if __name__ == "__main__":
    try:
        page = 1
        while True:
            display_view()
            state = node.query_full_status()
            ch = state["release_channel"]
            
            if page == 1:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 1/3] ({ch}):[/bold cyan]")
                rprint("  [1] 📥 Receive Funds (View Address & QR Data)")
                rprint("  [2] 💸 Send Transaction (Custom Fee Selection & Poison Guard)")
                rprint("  [3] 🌉 Initiate HTLC Cross-Chain Bridge Swap")
                rprint("  [4] 🎵 Open Decentralized Media & Download Center")
                rprint("  [5] ➡️  Go to Menu Page 2")
                rprint("  [6] 🚪 Exit System")
                choice = input("\nSelect [1-6]: ").strip()
                if choice == "1":
                    rprint(f"\n[bold green]Your Receiving Address:[/bold green]\n  {state['wallet']['address']}")
                    input("\nPress [Enter] to return...")
                elif choice == "2":
                    rprint("\n[bold cyan]Protected Transfer Terminal:[/bold cyan]")
                    recipient = input("Enter recipient address: ").strip()
                    try:
                        amount = float(input("Enter amount of FOX to send: ").strip())
                        fee_rate = 0.5
                        check = node.verify_address(recipient)
                        rprint(f"\n[yellow]Address Verification:[/yellow] {check}")
                        if input("Confirm send? (y/N): ").strip().lower() == 'y':
                            res = node.send_transaction_with_fee(recipient, amount, fee_rate)
                            rprint(f"\n[green]Result:[/green] {res}")
                    except ValueError:
                        rprint("[red]Invalid input.[/red]")
                    input("\nPress [Enter] to return...")
                elif choice == "3":
                    rprint("\n[bold cyan]Cross-Chain HTLC Bridge:[/bold cyan]")
                    target_chain = input("Destination chain (e.g. EVM-L2): ").strip() or "EVM-L2"
                    try:
                        amt = float(input("Amount to lock: ").strip() or "10")
                        res = node.initiate_htlc_bridge(amt, target_chain)
                        rprint(f"\n[green]Locked Successfully:[/green] {res}")
                    except ValueError:
                        rprint("[red]Invalid input.[/red]")
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    rprint("\n[bold cyan]Decentralized Media & Download Center (Audius-Style):[/bold cyan]")
                    catalog = node.get_media_catalog()
                    for item in catalog:
                        status = "[green]Downloaded[/green]" if item[5] else "[yellow]Available for Sync[/yellow]"
                        rprint(f"  • ID: [cyan]{item[0]}[/cyan] | {item[1]} by {item[2]} ({item[4]} MB) - {status}")
                    tid = input("\nEnter Track ID to download/cache locally (or press Enter): ").strip()
                    if tid:
                        res = node.download_media_track(tid)
                        rprint(f"\n[green]Download Complete:[/green] {res}")
                    input("\nPress [Enter] to return...")
                elif choice == "5":
                    page = 2
                elif choice == "6":
                    break
            elif page == 2:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 2/3] ({ch}):[/bold cyan]")
                rprint("  [1] 📜 View Transaction History Ledger")
                rprint("  [2] 📇 Manage Trusted Contacts (Address Book)")
                rprint("  [3] ◈ Execute Protected DEX Swap (10 FOX)")
                rprint("  [4] 🗺️ View Project Roadmap & Listing Milestones")
                rprint("  [5] ➡️  Go to Menu Page 3")
                rprint("  [6] ⬅️  Return to Menu Page 1")
                choice = input("\nSelect [1-6]: ").strip()
                if choice == "1":
                    rprint("\n[bold cyan]Transaction Ledger History:[/bold cyan]")
                    for t in node.get_transaction_history():
                        rprint(f"  • TX: {t[0]} | Amt: {t[2]} FOX | To: {t[4]}")
                    input("\nPress [Enter] to return...")
                elif choice == "2":
                    addr = input("Contact address: ").strip()
                    alias = input("Contact alias: ").strip()
                    if addr and alias:
                        rprint(f"\n[green]{node.add_trusted_contact(addr, alias)['message']}[/green]")
                    input("\nPress [Enter] to return...")
                elif choice == "3":
                    res = node.execute_protected_swap_query(10.0)
                    rprint(f"\n[green]Swap Result:[/green] {res}")
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    rm = state.get("roadmap", {})
                    rprint(Panel(f"[bold]Phase:[/bold] {rm.get('current_phase')}\n[bold]Milestone:[/bold] {rm.get('next_milestone')}", title="Roadmap", border_style="cyan"))
                    input("\nPress [Enter] to return...")
                elif choice == "5":
                    page = 3
                elif choice == "6":
                    page = 1
            elif page == 3:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 3/3] ({ch}):[/bold cyan]")
                rprint("  [1] 🔄 Toggle Release Channel (BETA ⇄ DEV)")
                rprint("  [2] 💾 Backup Database (VACUUM INTO Snapshot)")
                rprint("  [3] ⬅️  Return to Menu Page 2")
                rprint("  [4] 🚪 Exit System")
                choice = input("\nSelect [1-4]: ").strip()
                if choice == "1":
                    toggle_release_channel()
                    manifest = load_manifest()
                    node.config = manifest
                    rprint(f"\n[green]Channel switched to: {manifest.get('release_channel')}[/green]")
                    time.sleep(1)
                elif choice == "2":
                    res = node.create_live_backup()
                    rprint(f"\n[green]Backup Secured:[/green] {res}")
                    input("\nPress [Enter] to return...")
                elif choice == "3":
                    page = 2
                elif choice == "4":
                    break
    except KeyboardInterrupt:
        pass
