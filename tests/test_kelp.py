from typer.testing import CliRunner
from kelp import app

runner = CliRunner()

def test_kelp_init():
    result = runner.invoke(app, ["init", "--profile", "test_kelp_profile.yaml"])
    assert result.exit_code == 0
    assert "Vault initialized" in result.stdout
    import os
    if os.path.exists("test_kelp_profile.yaml"):
        os.remove("test_kelp_profile.yaml")
