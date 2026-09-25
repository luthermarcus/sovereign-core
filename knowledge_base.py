import sqlite3
import urllib.request
import urllib.error
import json
import time
import os

class ProtocolKnowledgeBase:
    """
    Automated Reconnaissance Engine:
    Tracks upstream ERC-4337 Account Abstraction and network dependencies.
    """
    def __init__(self, db_path="/home/luther/node-stack/ecosystem_metrics.db"):
        self.db_path = db_path
        self._init_db()
        self.TARGET_REPOS = [
            "eth-infinitism/account-abstraction", 
            "ethereum/go-ethereum",               
            "mysteriumnetwork/node",
            "AppArmor/apparmor"
        ]

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path) if '/' in self.db_path else '.', exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS protocol_knowledge_base (
                repo_name TEXT PRIMARY KEY,
                latest_stable_tag TEXT,
                latest_stable_date TEXT,
                latest_prerelease_tag TEXT,
                latest_prerelease_date TEXT,
                last_checked REAL
            )
        ''')
        conn.commit()
        conn.close()

    def fetch_upstream_intelligence(self):
        print("\n\033[95m=== SOVEREIGN KNOWLEDGE BASE: UPSTREAM RECON ===\033[0m")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for repo in self.TARGET_REPOS:
            url = f"https://api.github.com/repos/{repo}/releases"
            req = urllib.request.Request(url, headers={'User-Agent': 'Sovereign-Core-Node'})
            
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    stable_tag, stable_date = "None", "N/A"
                    pre_tag, pre_date = "None", "N/A"

                    for release in data:
                        if release.get('prerelease') == True and pre_tag == "None":
                            pre_tag = release.get('tag_name', 'Unknown')
                            pre_date = release.get('published_at', 'N/A')[:10]
                        elif release.get('prerelease') == False and stable_tag == "None":
                            stable_tag = release.get('tag_name', 'Unknown')
                            stable_date = release.get('published_at', 'N/A')[:10]
                        if stable_tag != "None" and pre_tag != "None":
                            break

                    cursor.execute('''
                        INSERT OR REPLACE INTO protocol_knowledge_base 
                        (repo_name, latest_stable_tag, latest_stable_date, latest_prerelease_tag, latest_prerelease_date, last_checked)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (repo, stable_tag, stable_date, pre_tag, pre_date, time.time()))
                    conn.commit()

                    print(f"\033[96m[{repo}]\033[0m")
                    print(f"  └── STABLE      : \033[92m{stable_tag}\033[0m ({stable_date})")
                    if pre_tag != "None":
                        print(f"  └── PRE-RELEASE : \033[93m{pre_tag}\033[0m ({pre_date} - \033[91mFLAGGED FOR PREP\033[0m)")
                    else:
                        print("  └── PRE-RELEASE : None active")

            except urllib.error.HTTPError as e:
                print(f"\033[91m[Error]\033[0m Failed hitting {repo} - {e.code}")
            
            time.sleep(1)

        conn.close()
        print("\033[95m================================================\033[0m\n")

if __name__ == "__main__":
    recon = ProtocolKnowledgeBase()
    recon.fetch_upstream_intelligence()
