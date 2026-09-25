#!/bin/bash

echo -e "\n\033[95m=== SOVEREIGN CORE: MASTER SYNC & BACKUP ===\033[0m"

# 1. Local Database Backup
DB_PATH="/home/luther/node-stack/ecosystem_metrics.db"
BACKUP_PATH="/home/luther/node-stack/backups/ecosystem_metrics_$(date +%Y%m%d_%H%M%S).db"

if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_PATH"
    echo -e "[\033[92m+\033[0m] SQLite Telemetry backed up successfully."
else
    echo -e "[\033[93m!\033[0m] No active database found to backup."
fi

# 2. Push Private Main Stack via HTTPS
echo -e "\n[\033[96m>\033[0m] Syncing Private Sovereign Core (Main Stack)..."
cd /home/luther/node-stack
git add .
git commit -m "chore: automated state sync & backup" || echo "No changes to commit."
git push origin main || echo -e "[\033[91mX\033[0m] Main stack sync failed."

# 3. Push Public Standalone Template via HTTPS
echo -e "\n[\033[96m>\033[0m] Syncing Public Standalone Paymaster..."
cd /home/luther/sovereign-ethical-paymaster
git add .
git commit -m "chore: automated state sync" || echo "No changes to commit."
git push origin main || echo -e "[\033[91mX\033[0m] Standalone sync failed."

echo -e "\n\033[95m============================================\033[0m\n"
