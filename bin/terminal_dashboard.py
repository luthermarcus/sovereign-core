#!/usr/bin/env python3
import sys
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, RichLog
from textual.containers import ScrollableContainer, Vertical

sys.path.append(os.path.dirname(__file__))
from sovereign_core import SovereignNode

node = SovereignNode(is_regtest=True)

class SovereignTerminalUI(App):
    CSS = """
    Screen { 
        background: #0f1115; 
        color: #dcdcdc; 
        layout: vertical; 
    }
    Header { background: #181b22; color: #4CAF50; text-style: bold; height: 3; }
    Footer { background: #181b22; color: #888; height: 3; }
    
    ScrollableContainer {
        height: 1fr;
        width: 100%;
    }

    .card { 
        background: #181b22; 
        border: solid #2a2e39; 
        padding: 1; 
        margin: 1; 
        height: auto;
    }
    
    Button { 
        margin-top: 1; 
        width: 100%; 
        background: #2563eb; 
        color: #fff; 
        height: 3;
    }
    Button.warning { background: #d97706; }
    
    #log-card {
        height: 1fr;
        min-height: 8;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer():
            # 1. Dynamic Hardware Profile Card
            with Vertical(classes="card", id="metrics-card"):
                yield Static(f"[bold green]📊 Hardware Profile:[/bold green] {node.tier}")
                yield Static(f"Details: {node.tier_desc}")
                yield Static("Faucet Reserve: Loading...", id="metrics-display")
            
            # 2. Adaptive Controls Card
            with Vertical(classes="card", id="controls-card"):
                yield Static("[bold green]🛡️ Adaptive IoT Quick Controls[/bold green]")
                yield Button("Simulate Fast Micro-Payment", id="btn-micro")
                yield Button("Run Self-Healing Diagnostics", id="btn-heal", classes="warning")
            
            # 3. Fluid System Log Card
            with Vertical(classes="card", id="log-card"):
                yield Static("[bold green]💻 Dynamic System Log[/bold green]")
                yield RichLog(id="terminal-log", highlight=True, markup=True)
                
        yield Footer()

    def on_mount(self) -> None:
        self.update_metrics()
        log = self.query_one("#terminal-log", RichLog)
        log.write("[green]>[/green] Sovereign Core v0.2.8-beta online.")
        log.write(f"[green]>[/green] Initial dimensions: {self.size.width} cols x {self.size.height} rows")
        log.write(f"[green]>[/green] Hardware adaptation active: [bold cyan]{node.tier}[/bold cyan]")

    def on_resize(self, event) -> None:
        """Dynamically captures terminal dimension shifts when keyboards open/close."""
        try:
            log = self.query_one("#terminal-log", RichLog)
            log.write(f"[dim]⚡ Viewport adjusted: {event.size.width}x{event.size.height}[/dim]")
        except Exception:
            pass

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
                log.write(f"[yellow]>[/yellow] Micro-payment buffered (Buffer: {res['buffer_size']}/3)")
            else:
                log.write(f"[green]✓[/green] Batch committed {res['count']} micro-payments to WAL.")
                self.update_metrics()
        elif btn_id == "btn-heal":
            log.write("[yellow]>[/yellow] Running autonomous health check...")
            report = node.doctor.run_health_check_and_heal()
            log.write(f"[green]✓[/green] Status: [bold]{report['status']}[/bold]")
            for action in report["actions_taken"]:
                log.write(f"  [cyan]⚡ Action:[/cyan] {action}")

if __name__ == "__main__":
    app = SovereignTerminalUI()
    app.run()
