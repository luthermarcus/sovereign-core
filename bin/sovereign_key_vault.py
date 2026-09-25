#!/usr/bin/env python3
import os, hashlib, base64, json

class SelfCustodyKeyVault:
    def __init__(self):
        self.vault_dir = os.path.expanduser("~/sovereign-ecosystem/vault")
        os.makedirs(self.vault_dir, exist_ok=True)
        self.seed_path = os.path.join(self.vault_dir, "user_sovereign.seed")
        self._initialize_user_keys()

    def _initialize_user_keys(self):
        if not os.path.exists(self.seed_path):
            raw_entropy = os.urandom(32)
            mnemonic_placeholder = base64.b64encode(raw_entropy).decode()
            pubkey_hash = hashlib.sha256(raw_entropy).hexdigest()[:40]
            
            vault_payload = {
                "owner_sovereign_address": f"sov1{pubkey_hash}",
                "client_seed_entropy": mnemonic_placeholder,
                "custody_type": "100%_SELF_OWNED",
                "warning": "KEEP THIS SEED SECURE. NO SERVER HOLDS A BACKUP."
            }
            with open(self.seed_path, 'w') as f:
                json.dump(vault_payload, f, indent=2)
            os.chmod(self.seed_path, 0o600)

    def get_user_vault_details(self):
        try:
            with open(self.seed_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    vault = SelfCustodyKeyVault()
    print(json.dumps(vault.get_user_vault_details(), indent=2))
