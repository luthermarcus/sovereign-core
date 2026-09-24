# Sovereign Core Technical Whitepaper (v0.2.1-beta)
## 1. Abstract
Sovereign Core establishes an ultra-lightweight settlement engine anchored to Bitcoin SPV. By offloading transaction execution to local SQLite WAL ledgers, consumer edge devices participate in consensus without base-layer bloat.

## 2. 5/5/90 Revenue Routing & Ledger Pruning
Every transaction enforces a strict split (5% Creator, 5% Treasury, 90% DePIN). To maintain zero-bloat on 24/7 edge nodes, the architecture integrates a daily SQLite VACUUM protocol to permanently reclaim physical hard drive space.
