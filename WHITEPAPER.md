# Sovereign Core: A Bare-Metal, Hardware-Adaptive Bitcoin & DePIN Ecosystem

## Abstract
Sovereign Core proposes a return to pure decentralization. By combining Bitcoin's SPV with local SQLite WAL ledgers and WASI execution sandboxes, it enables users on vintage hardware (x86/Termux) to participate fully in a decentralized physical infrastructure network (DePIN).

## Architecture
- **Consensus:** Bitcoin SPV (Simplified Payment Verification).
- **State Management:** SQLite running in WAL mode to protect against power loss.
- **The WASI Enclave:** Apps run inside a strict WebAssembly sandbox to protect wallet keys.
- **Economics:** In-wallet Automated Market Maker (AMM) with Liquidity Bootstrapping Pools (LBPs) and Upstream Dependency Splitting (fork royalties).
