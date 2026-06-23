import yaml
import os

class Vault:
    def __init__(self, profile_path="profile.yaml"):
        self.profile_path = profile_path
        self.template = {
            "target_data": {
                "name": "YOUR_FULL_NAME",
                "email": "YOUR_EMAIL@EXAMPLE.COM",
                "phone": "YOUR_PHONE_NUMBER",
                "usernames": ["user1", "user2"]
            }
        }

    def init_profile(self):
        if not os.path.exists(self.profile_path):
            with open(self.profile_path, 'w') as f:
                yaml.dump(self.template, f, default_flow_style=False)
            return True
        return False

    def load_profile(self):
        if not os.path.exists(self.profile_path):
            raise FileNotFoundError(f"Profile not found at {self.profile_path}")
        with open(self.profile_path, 'r') as f:
            return yaml.safe_load(f)
