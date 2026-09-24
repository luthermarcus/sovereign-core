#!/usr/bin/env python3
import sys
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, RichLog
from textual.containers import Container, Horizontal, Vertical

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode

node = SovereignNode(is_regtest=True)

class SovereignTerminalUI(App):
    CSS = """
    Screen { background: #0f1115; color: #dcdcdc; }
    Header { background: #181b22; color: #4CAF50; text-style: bold; }
    Footer { background: #181b22; color: #888; }
    .card { background: #181b22; border: solid #2a2e39; padding: 1; margin: 1; height: 1fr; }
    #metrics-box { dock: top; height: 7; }
    #console-box { height: 1fr; }
    Button { margin-top: 1; width: 100%; background: #2563eb; color: #fff; }
    Button.warning { background: #d97706; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            with Vertical(classes="card", id="metrics-box"):
                yield Static("[bold green]📊 Sovereign Core Node Telemetry[/bold green]")
                yield Static(id="metrics-display", value="Loading ledger stats...")
            with Horizontal():
                with Vertical(classes="card"):
                    yield Static("[bold green]⚙️ DePIN Compute & Controls[/bold green]")
                    yield Button("Mine Proof-of-Compute (10 FOX)", id="btn-poc")
                    yield Button("Run '--doctor' Diagnostics", id="btn-doctor", classes="warning")
                    yield Button("Prune SQLite Storage", id="btn-prune", classes="warning")
                with Vertical(classes="card", id="console-box"):
                    yield Static("[bold green]💻 Live Node Terminal Log[/bold green]")
                    yield RichLog(id="terminal-log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.update_metrics()
        self.set_interval(5.0, self.update_metrics)
        log = self.query_one("#terminal-log", RichLog)
        log.write("[green]>[/green] Sovereign Terminal UI v0.2.2 initialized.")

    def update_metrics(self) -> None:
        with node.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM accounts WHERE address = 'genesis_faucet'")
            faucet = cur.fetchone()[0]
            cur.execute("SELECT balance FROM accounts WHERE address = 'depin_pool'")
            depin = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM depin_proofs")
            proofs = cur.fetchone()[0]
        
        display = self.query_one("#metrics-display", Static)
        display.update(f"Faucet Reserve: [bold white]{faucet:.2f} FOX[/bold white]  |  DePIN Pool: [bold white]{depin:.2f} FOX[/bold white]  |  Verified PoC Blocks: [bold white]{proofs}[/bold white]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#terminal-log", RichLog)
        btn_id = event.button.id
        
        if btn_id == "btn-poc":
            log.write("[yellow]>[/yellow] Solving SHA-256 Proof-of-Compute puzzle...")
            res = node.record_compute_proof("terminal_node")
            log.write(f"[green]✓[/green] PoC Mined! Nonce: {res['nonce']} | Hash: {res['hash'][:16]}... (+10 FOX)")
            self.update_metrics()
            
        elif btn_id == "btn-doctor":
            log.write("[yellow]>[/yellow] Running NodeDoctor diagnostics...")
            report = node.doctor.run_diagnostics()
            for c in report["checks"]:
                status_icon = "[green]✓[/green]" if c["passed"] else "[red]✗[/red]"
                log.write(f"  {status_icon} {c['name']}: {c['detail']}")
            log.write(f"[green]✓[/green] System State: [bold]{report['status']}[/bold]")
            
        elif btn_id == "btn-prune":
            log.write("[yellow]>[/yellow] Vacuuming SQLite database...")
            prune = node.prune_ledger(keep_days=7)
            log.write(f"[green]✓[/green] Storage optimized. Cleared {prune['cleared_records']} stale records.")
            self.update_metrics()

if __name__ == "__main__":
    app = SovereignTerminalUI()
    app.run()
