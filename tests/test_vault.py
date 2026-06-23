from src.vault import Vault

def test_vault_init_and_load(temp_profile):
    vault = Vault(temp_profile)
    vault.init_profile()
    data = vault.load_profile()
    
    assert "target_data" in data
    assert "name" in data["target_data"]
    assert "email" in data["target_data"]
