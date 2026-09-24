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
    #metrics-box { dock: top; height: 8; }
    #console-box { height: 1fr; }
    Button { margin-top: 1; width: 100%; background: #2563eb; color: #fff; }
    Button.warning { background: #d97706; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            with Vertical(classes="card", id="metrics-box"):
                yield Static(f"[bold green]📊 IoT Node Profile: {node.tier}[/bold green] ({node.tier_desc})")
                yield Static("Initializing autonomous telemetry...", id="metrics-display")
            with Horizontal():
                with Vertical(classes="card"):
                    yield Static("[bold green]🛡️ Autonomous IoT Controls[/bold green]")
                    yield Button("Simulate Fast Micro-Payment", id="btn-micro")
                    yield Button("Run Self-Healing Diagnostics", id="btn-heal", classes="warning")
                with Vertical(classes="card", id="console-box"):
                    yield Static("[bold green]💻 Autonomous System Log[/bold green]")
                    yield RichLog(id="terminal-log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.update_metrics()
        log = self.query_one("#terminal-log", RichLog)
        log.write("[green]>[/green] Sovereign Core v0.2.5-beta (IoT Edition) online.")
        log.write(f"[green]>[/green] Hardware profile: [bold cyan]{node.tier}[/bold cyan]")
        log.write("[green]>[/green] Autonomous self-healing anomaly detector active.")

    def update_metrics(self) -> None:
        with node.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM accounts WHERE address = 'genesis_faucet'")
            faucet = cur.fetchone()[0]
        display = self.query_one("#metrics-display", Static)
        display.update(f"Faucet Reserve: [bold white]{faucet:.2f} FOX[/bold white]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#terminal-log", RichLog)
        btn_id = event.button.id
        if btn_id == "btn-micro":
            res = node.process_batched_micro_payment("genesis_faucet", "micro_recipient", 5.0)
            if res["status"] == "buffered":
                log.write(f"[yellow]>[/yellow] Micro-payment buffered in memory (Buffer size: {res['buffer_size']}/3)")
            else:
                log.write(f"[green]✓[/green] Batch committed {res['count']} micro-payments to SQLite WAL.")
                self.update_metrics()
        elif btn_id == "btn-heal":
            log.write("[yellow]>[/yellow] Running autonomous health check...")
            report = node.doctor.run_health_check_and_heal()
            log.write(f"[green]✓[/green] System Health Status: [bold]{report['status']}[/bold]")
            for action in report["actions_taken"]:
                log.write(f"  [cyan]⚡ Self-Heal Action:[/cyan] {action}")

if __name__ == "__main__":
    app = SovereignTerminalUI()
    app.run()
