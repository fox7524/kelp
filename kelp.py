import typer
from src.vault import Vault
from src.scanner import Scanner
from src.takedown import Enforcer
from src.legal import LegalEngine

app = typer.Typer(help="Kelp - Digital Footprint Cleaner")

@app.command()
def init(profile: str = "profile.yaml"):
    """Initialize a new data vault profile."""
    vault = Vault(profile)
    if vault.init_profile():
        typer.secho(f"Vault initialized at {profile}. Please edit it with your details.", fg=typer.colors.GREEN)
    else:
        typer.secho(f"Vault already exists at {profile}.", fg=typer.colors.YELLOW)

@app.command()
def scan(profile: str = "profile.yaml"):
    """Scan for exposed data."""
    vault = Vault(profile)
    data = vault.load_profile()
    
    scanner = Scanner()
    results = scanner.scan(data["target_data"])
    
    for res in results:
        typer.secho(f"[FOUND] {res['type'].upper()} at {res['url']}", fg=typer.colors.RED)
    
    return results

@app.command()
def enforce(profile: str = "profile.yaml"):
    """Run takedown enforcement on found exposures."""
    # Re-run scan for MVP simplicity
    results = scan(profile)
    
    vault = Vault(profile)
    data = vault.load_profile()
    
    enforcer = Enforcer()
    engine = LegalEngine()
    
    for res in results:
        enf_data = enforcer.lookup_domain(res["domain"])
        email_content = engine.draft_email(data["target_data"], res, enf_data)
        engine.send_email(email_content)
        typer.secho(f"Sent takedown notice to {enf_data['abuse_email']} for {res['domain']}", fg=typer.colors.GREEN)

if __name__ == "__main__":
    app()