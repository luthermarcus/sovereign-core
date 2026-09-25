# Sovereign Core (v2.8.1-beta)

Ultra-lightweight, hardware-adaptive Bitcoin and DePIN settlement micro-OS layer operated via mobile Termux or Linux terminals.

## What's New in v2.8.1-beta
- **Self-Pruning Beta Telemetry:** Automatically records community feedback and diagnostic flags during beta testing, with automated database table pruning (`DROP TABLE IF EXISTS`) when transitioning to LIVE/Mainnet production.
- **Community Feedback Portal:** Dedicated TUI submenu enabling developers and testers to log system improvement ideas, bug reports, and feature requests directly into local SQLite WAL storage.
- **App Simulation Harness:** Interactive test suite simulating high-frequency transaction loads, P2P peer handshake latency, and storage cap guard stress tests.
- **Resilient SQLite WAL Architecture:** Memory-mapped I/O (`mmap_size`), ACID compliance, and autonomous boot diagnostics.
