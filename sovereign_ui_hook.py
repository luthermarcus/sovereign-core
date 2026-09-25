import sqlite3
import os

def display_sovereign_telemetry():
    db_path = "/home/luther/node-stack/ecosystem_metrics.db"
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n\033[95m=== SOVEREIGN CORE: TREASURY & RECON TELEMETRY ===\033[0m")
    
    # 1. Fetch Treasury Status
    try:
        cursor.execute("SELECT SUM(tax_collected), SUM(gas_sponsored) FROM paymaster_treasury_log")
        row = cursor.fetchone()
        active_pool = (row[0] or 0.0) - (row[1] or 0.0)
        print(f"Active Treasury Gas Pool : \033[96m${active_pool:.2f}\033[0m")
    except sqlite3.OperationalError:
        print("Active Treasury Gas Pool : \033[93m$0.00 (Awaiting Data)\033[0m")

    # 2. Fetch Recon Alerts
    try:
        cursor.execute("SELECT repo_name, latest_prerelease_tag FROM protocol_knowledge_base WHERE latest_prerelease_tag != 'None'")
        flags = cursor.fetchall()
        if flags:
            print("\n\033[91m[!] CRITICAL UPSTREAM FLAGS PENDING PREPARATION:\033[0m")
            for repo, tag in flags:
                print(f" -> {repo}: \033[93m{tag}\033[0m")
        else:
            print("\033[92m[v] Upstream Protocol Dependencies Stable. No flags.\033[0m")
    except sqlite3.OperationalError:
        pass

    print("\033[95m==================================================\033[0m\n")
    conn.close()

if __name__ == "__main__":
    display_sovereign_telemetry()
