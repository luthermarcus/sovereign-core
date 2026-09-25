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

def display_main_header():
    console.clear()
    state = node.query_full_status()
    flags = state["flags"]

    tbl = Table(show_header=False, box=None, expand=True)
    tbl.add_column("Key", style="cyan", ratio=1, no_wrap=True)
    tbl.add_column("Val", style="bold white", justify="right", ratio=1, no_wrap=True)

    active_flags = [f for f in flags if f["status"] == "ACTIVE"]
    if not active_flags:
        tbl.add_row("--- [bold yellow]📡 Security & Flags[/bold yellow] ---", "---")
        tbl.add_row("System Integrity", "[bold green]● ALL FLAGS GREEN[/bold green]")
    else:
        for f in active_flags:
            col = "red" if f["level"] == "CRITICAL" else "yellow"
            tbl.add_row(f"FLAG: {f['key'][:12]}", f"[{col}]{f['message'][:22]}[/{col}]")

    st = state["storage"]
    tbl.add_row("--- [bold magenta]💾 Local Storage & Mail[/bold magenta] ---", "---")
    tbl.add_row("Local Allocation", f"{st['used_mb']:.1f} MB / {st['cap_mb']} MB Used")
    tbl.add_row("Encrypted Inbox", f"{state['unread_mail']} Unread Messages")
    tbl.add_row("Cached Audio Tracks", f"{state['media_downloaded']} Downloaded (IPFS)")
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
                rprint("  [3] 🌉 Initiate HTLC Cross-Chain Bridge Swap")
                rprint("  [4] ✉️ Encrypted Web3 Mail & Local Storage Dashboard")
                rprint("  [5] ➡️  Go to Menu Page 2")
                rprint("  [6] 🚪 Exit System")
                choice = input("\nSelect [1-6]: ").strip()
                
                if choice == "1":
                    console.clear()
                    rprint(Panel(f"[bold green]Receiving Dashboard[/bold green]\n\nYour Sovereign Address:\n[cyan]{state['wallet']['address']}[/cyan]\n\nBalances:\n• {state['wallet']['fox']} FOX\n• {state['wallet']['sats']} SATS", title="[Receive Menu]", border_style="cyan"))
                    input("\nPress [Enter] to return to dashboard...")
                elif choice == "2":
                    console.clear()
                    rprint(Panel("[bold cyan]Protected Transfer Dashboard[/bold cyan]", title="[Send Menu]", border_style="cyan"))
                    recipient = input("Enter recipient address: ").strip()
                    if recipient:
                        try:
                            amount = float(input("Enter amount of FOX to send: ").strip())
                            check = node.verify_address(recipient)
                            rprint(f"\n[yellow]Address Verification Check:[/yellow] {check}")
                            if input("Confirm send? (y/N): ").strip().lower() == 'y':
                                res = node.send_transaction_with_fee(recipient, amount, 0.5)
                                rprint(f"\n[green]Transaction Result:[/green] {res}")
                        except ValueError:
                            rprint("[red]Invalid amount entered.[/red]")
                    input("\nPress [Enter] to return...")
                elif choice == "3":
                    console.clear()
                    rprint(Panel("[bold cyan]HTLC Cross-Chain Bridge Dashboard[/bold cyan]", title="[Bridge Menu]", border_style="cyan"))
                    target = input("Destination chain (e.g. EVM-L2): ").strip() or "EVM-L2"
                    try:
                        amt = float(input("Amount to lock: ").strip() or "10")
                        res = node.initiate_htlc_bridge(amt, target)
                        rprint(f"\n[green]Bridge Locked Successfully:[/green] {res}")
                    except ValueError:
                        rprint("[red]Invalid input.[/red]")
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    console.clear()
                    inbox = node.get_inbox_messages()
                    mail_summary = "\n".join([f"• [{m[0]}] {m[1]} -> {m[2]}" for m in inbox])
                    rprint(Panel(f"[bold cyan]Encrypted Mail & Local Storage Dashboard[/bold cyan]\n\nStorage Used: {state['storage']['used_mb']:.1f} MB / {state['storage']['cap_mb']} MB\n\n[bold]Inbox Messages:[/bold]\n{mail_summary}", title="[Mail Center]", border_style="magenta"))
                    
                    action = input("\nSend new secure local message? (y/N): ").strip().lower()
                    if action == 'y':
                        recip = input("Recipient: ").strip()
                        subj = input("Subject: ").strip()
                        body = input("Body: ").strip()
                        if recip and subj:
                            res = node.send_encrypted_mail(recip, subj, body)
                            rprint(f"\n[green]Dispatched:[/green] {res}")
                    input("\nPress [Enter] to return...")
                elif choice == "5":
                    page = 2
                elif choice == "6":
                    break
                    
            elif page == 2:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 2/3] ({ch}):[/bold cyan]")
                rprint("  [1] 🎵 Open Decentralized Media & Download Center")
                rprint("  [2] 📜 View Transaction History Ledger Dashboard")
                rprint("  [3] 📇 Manage Trusted Contacts (Address Book)")
                rprint("  [4] ◈ Execute Protected DEX Swap (10 FOX)")
                rprint("  [5] ➡️  Go to Menu Page 3")
                rprint("  [6] ⬅️  Return to Menu Page 1")
                choice = input("\nSelect [1-6]: ").strip()
                
                if choice == "1":
                    console.clear()
                    catalog = node.get_media_catalog()
                    cat_summary = "\n".join([f"• [{item[0]}] {item[1]} by {item[2]} ({item[4]}MB) - {'[Downloaded]' if item[5] else '[Available]'}" for item in catalog])
                    rprint(Panel(f"[bold cyan]Decentralized Media Dashboard[/bold cyan]\n\n{cat_summary}", title="[Media Center]", border_style="magenta"))
                    tid = input("\nEnter Track ID to sync locally (or press Enter): ").strip()
                    if tid:
                        res = node.download_media_track(tid)
                        rprint(f"\n[green]Sync Result:[/green] {res}")
                    input("\nPress [Enter] to return...")
                elif choice == "2":
                    console.clear()
                    txs = node.get_transaction_history()
                    tx_summary = "\n".join([f"• {t[0]} | {t[1]} {t[2]} FOX | To: {t[4]}" for t in txs])
                    rprint(Panel(f"[bold cyan]Transaction Ledger Dashboard[/bold cyan]\n\n{tx_summary}", title="[Ledger]", border_style="green"))
                    input("\nPress [Enter] to return...")
                elif choice == "3":
                    console.clear()
                    rprint(Panel("[bold cyan]Trusted Contacts Address Book[/bold cyan]", title="[Contacts]", border_style="cyan"))
                    addr = input("Contact address: ").strip()
                    alias = input("Contact alias: ").strip()
                    if addr and alias:
                        rprint(f"\n[green]{node.add_trusted_contact(addr, alias)['message']}[/green]")
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    console.clear()
                    res = node.execute_protected_swap_query(10.0)
                    rprint(Panel(f"[bold cyan]DEX Swap Dashboard[/bold cyan]\n\nResult: {res}", title="[AMM DEX]", border_style="green"))
                    input("\nPress [Enter] to return...")
                elif choice == "5":
                    page = 3
                elif choice == "6":
                    page = 1
                    
            elif page == 3:
                rprint(f"\n[bold cyan]Bare-Metal Operations Menu [Page 3/3] ({ch}):[/bold cyan]")
                rprint("  [1] 🗺️ View Project Roadmap & Listing Milestones")
                rprint("  [2] 🔄 Toggle Release Channel (BETA ⇄ DEV)")
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
                    time.sleep(1)
                elif choice == "3":
                    console.clear()
                    res = node.create_live_backup()
                    rprint(Panel(f"[bold cyan]Backup Dashboard[/bold cyan]\n\nSnapshot Result: {res}", title="[Backup]", border_style="green"))
                    input("\nPress [Enter] to return...")
                elif choice == "4":
                    page = 2
                elif choice == "5":
                    break
    except KeyboardInterrupt:
        pass
