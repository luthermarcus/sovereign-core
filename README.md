# Sovereign Core (v0.2.1-beta Master Build)
**Hardware-Adaptive Bitcoin & DePIN Settlement Layer**

![Version](https://img.shields.io/badge/version-v0.2.1--beta-blue)
![Consensus](https://img.shields.io/badge/consensus-SPV%20%2B%20Taproot-green)

Sovereign Core anchors local SQLite WAL execution engines to Bitcoin via Taproot commitments. It harvests idle CPU cycles from edge hardware while providing an air-gapped PSBT wallet, WASI execution sandbox, and automated disk space pruning.

### 💻 Hardware Compatibility Matrix

| Platform | Environment | Recommended Role | Performance Profile |
| :--- | :--- | :--- | :--- |
| **Raspberry Pi 4 / 5** | Linux (Debian/Ubuntu) | Always-On Harvester & Relayer | High (PID thermal throttling active) |
| **Vintage x86 Laptops** | Linux Mint / Alpine | DePIN Compute & Local Host | Maximum compute throughput |
| **Android Smartphones** | Termux / PRoot | Edge Client & Signer | Ultra-low power; immune to OS killers |
| **Hardware Wallets** | Coldcard, Blockstream Jade | Air-Gapped Key Custody | Zero network exposure via BIP-174 PSBT |

### 🚀 Launch & Install Guide
1. **Launch the Node Engine:** `python3 bin/sovereign_core.py --regtest`
2. **Start the API Daemon:** `python3 bin/dashboard_api.py`
3. **Open the Wallet Interface:** Launch `dashboard.html` in your browser.
