#!/usr/bin/env python3
import os, sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

KB_CONTENT = """
# 📖 Sovereign Core Consensus & Knowledge Base

### 1. The BIP 9 Versionbits Consensus Mechanism
* **Decentralized Signaling:** Miners vote on network upgrades without giving custody to central developers.
* **Block Header Bits:** When a DePIN proof is mined, the header includes a version bit corresponding to an active proposal.
* **Activation Threshold:** Upgrades require a supermajority (**75%–95%**) within a defined epoch.
* **State Lifecycle:** `DEFINED` ➔ `STARTED` (Voting Open) ➔ `LOCKED_IN` (Threshold Achieved) ➔ `ACTIVE` (Enforced).

### 2. Economic Node Sovereignty (UASF / BIP 8)
* **User Activated Soft Forks (UASF):** If miners censor or stall a critical upgrade, validating edge nodes can flag `LOT=true` (Lock-in on Timeout) to force network-wide activation.
* **Economic Majority:** Exchanges and node operators reject blocks that fail to signal compliant bits.

### 3. Pre-Release Software Tracking
* **Checksum Verification:** New client versions must match their cryptographic SHA-256 binary hash before triggering consensus rules.
* **Anti-MEV Fair Trading:** Constant-product liquidity pools enforce hard price impact caps (**2.0%**) to prevent front-running and sandwich attacks.
"""

def display_kb():
    console.clear()
    console.print(Panel(Markdown(KB_CONTENT), title="[bold green]Sovereign Consensus Knowledge Base[/bold green]", border_style="cyan"))
    input("\nPress [Enter] to return to the control center...")

if __name__ == "__main__":
    display_kb()
