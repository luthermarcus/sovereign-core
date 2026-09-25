# Sovereign Core (v2.9.7-beta)

Ultra-lightweight, hardware-adaptive Bitcoin and DePIN settlement micro-OS layer operated via mobile Termux, Linux terminals, or containerized environments.

## What's New in v2.9.7-beta
- **Standalone Knowledge Crawler (`sovereign_crawler.py`):** Independent micro-service that maps external peer ecosystems and populates a local SQLite knowledge base while respecting firewall safety rules.
- **Firewall-Aware Discovery:** Automatically filters out blocked endpoints so the crawler never queries restricted or untrusted addresses.
- **Unbuffered Containerized TUI:** Immediate rendering of multi-page operations menus.

## Credits & Community Guidance
Developed collaboratively through community-inspired design patterns (Magisk/XDA modular package structures, BIP 9 Versionbits signaling, and secure SQLite WAL isolation).
