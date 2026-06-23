# Kelp Core MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP of Kelp, a modular Python CLI tool for automating digital footprint cleanup via OSINT scanning and automated legal takedown notices.

**Architecture:** A Python CLI application using `typer`. It uses a local `profile.yaml` as a secure data vault, a scanner module for OSINT simulation, a takedown module for infrastructure identification, and a legal engine using `jinja2` for drafting legally binding emails.

**Tech Stack:** Python 3, `typer`, `pyyaml`, `jinja2`, `pytest`

---

### Task 1: Project Setup and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write requirements.txt**

```text
typer==0.12.3
pyyaml==6.0.1
jinja2==3.1.4
pytest==8.2.2
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: Dependencies install successfully.

- [ ] **Step 3: Create tests/conftest.py for pytest**

```python
import pytest
import os
import tempfile

@pytest.fixture
def temp_profile():
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)
    yield path
    os.unlink(path)
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt tests/conftest.py
git commit -m "chore: setup project dependencies and pytest"
```

---

### Task 2: The Vault (`src/vault.py`)

**Files:**
- Create: `src/vault.py`
- Create: `tests/test_vault.py`

- [ ] **Step 1: Write the failing test**

```python
from src.vault import Vault

def test_vault_init_and_load(temp_profile):
    vault = Vault(temp_profile)
    vault.init_profile()
    data = vault.load_profile()
    
    assert "target_data" in data
    assert "name" in data["target_data"]
    assert "email" in data["target_data"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_vault.py -v`
Expected: FAIL (ModuleNotFoundError for src.vault)

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_vault.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/vault.py tests/test_vault.py
git commit -m "feat: implement local data vault"
```

---

### Task 3: The Scanner (`src/scanner.py`)

**Files:**
- Create: `src/scanner.py`
- Create: `tests/test_scanner.py`

- [ ] **Step 1: Write the failing test**

```python
from src.scanner import Scanner

def test_scanner_finds_exposures():
    scanner = Scanner()
    target_data = {"email": "test@example.com"}
    results = scanner.scan(target_data)
    
    assert len(results) > 0
    assert "url" in results[0]
    assert "type" in results[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
class Scanner:
    def __init__(self):
        pass

    def scan(self, target_data: dict) -> list:
        # Mock OSINT scan results for MVP
        email = target_data.get("email", "unknown")
        print(f"[*] Simulating OSINT scan for {email}...")
        
        return [
            {
                "url": "https://sketchy-broker.com/profile/test",
                "domain": "sketchy-broker.com",
                "type": "data_broker"
            },
            {
                "url": "https://paste-leak-site.net/raw/123",
                "domain": "paste-leak-site.net",
                "type": "data_leak"
            }
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/scanner.py tests/test_scanner.py
git commit -m "feat: implement simulated OSINT scanner"
```

---

### Task 4: The Takedown Enforcer (`src/takedown.py`)

**Files:**
- Create: `src/takedown.py`
- Create: `tests/test_takedown.py`

- [ ] **Step 1: Write the failing test**

```python
from src.takedown import Enforcer

def test_enforcer_lookup():
    enforcer = Enforcer()
    result = enforcer.lookup_domain("sketchy-broker.com")
    
    assert result["domain"] == "sketchy-broker.com"
    assert "abuse_email" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_takedown.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
class Enforcer:
    def __init__(self):
        pass

    def lookup_domain(self, domain: str) -> dict:
        # Mock WHOIS/DNS lookup for MVP
        print(f"[*] Simulating WHOIS lookup for {domain}...")
        
        return {
            "domain": domain,
            "host_provider": "MockHost LLC",
            "abuse_email": f"abuse@{domain}"
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_takedown.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/takedown.py tests/test_takedown.py
git commit -m "feat: implement takedown enforcer domain lookup"
```

---

### Task 5: The Legal Engine Templates (`templates/*.j2`)

**Files:**
- Create: `templates/ccpa_request.j2`
- Create: `templates/dmca_takedown.j2`

- [ ] **Step 1: Create CCPA template**

```jinja2
Subject: CCPA/GDPR Right to Deletion Request - {{ name }}

To the Privacy Officer at {{ domain }},

I am writing to formally request the immediate deletion of all personal information pertaining to me, {{ name }}, pursuant to the California Consumer Privacy Act (CCPA) and/or the General Data Protection Regulation (GDPR).

My identifying information is:
Email: {{ email }}
Phone: {{ phone }}

Your platform is currently hosting my data at: {{ url }}

Please confirm within 30 days that my data has been purged from your systems.

Sincerely,
{{ name }}
```

- [ ] **Step 2: Create DMCA template**

```jinja2
Subject: URGENT: DMCA Takedown / AUP Violation Notice

To the Abuse Department at {{ host_provider }} ({{ abuse_email }}),

I am writing to report a severe violation of your Acceptable Use Policy and/or a DMCA violation regarding stolen personal data hosted on your infrastructure.

The offending URL is: {{ url }}
Domain: {{ domain }}

This data belongs to {{ name }} ({{ email }}). 

I demand the immediate removal or suspension of this content. Failure to act may result in legal action.

Sincerely,
{{ name }}
```

- [ ] **Step 3: Commit**

```bash
git add templates/
git commit -m "feat: add legal email templates"
```

---

### Task 6: The Legal Engine Logic (`src/legal.py`)

**Files:**
- Create: `src/legal.py`
- Create: `tests/test_legal.py`

- [ ] **Step 1: Write the failing test**

```python
from src.legal import LegalEngine
import os

def test_generate_email():
    engine = LegalEngine(templates_dir="templates")
    
    target_data = {"name": "John Doe", "email": "john@example.com", "phone": "555-0100"}
    exposure = {"url": "http://bad.com/john", "domain": "bad.com", "type": "data_broker"}
    enforcement = {"host_provider": "BadHost", "abuse_email": "abuse@bad.com"}
    
    email_content = engine.draft_email(target_data, exposure, enforcement)
    
    assert "Right to Deletion Request - John Doe" in email_content
    assert "http://bad.com/john" in email_content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_legal.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
import os
from jinja2 import Environment, FileSystemLoader

class LegalEngine:
    def __init__(self, templates_dir="templates"):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def draft_email(self, target_data: dict, exposure: dict, enforcement: dict) -> str:
        template_name = "ccpa_request.j2" if exposure["type"] == "data_broker" else "dmca_takedown.j2"
        template = self.env.get_template(template_name)
        
        context = {**target_data, **exposure, **enforcement}
        return template.render(context)

    def send_email(self, content: str):
        # Mock SMTP sending for MVP
        print("\n--- DISPATCHING LEGAL NOTICE ---")
        print(content)
        print("--------------------------------\n")
        return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_legal.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/legal.py tests/test_legal.py
git commit -m "feat: implement legal engine email generator"
```

---

### Task 7: The CLI Entrypoint (`kelp.py`)

**Files:**
- Create: `kelp.py`
- Create: `tests/test_kelp.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_kelp.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_kelp.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kelp.py tests/test_kelp.py
git commit -m "feat: implement Typer CLI entrypoint"
```
