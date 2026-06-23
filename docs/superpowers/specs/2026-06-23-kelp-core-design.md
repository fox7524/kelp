# Kelp - Digital Footprint Cleaner (Core Design)

## Overview
Kelp is an aggressive, edge-of-ethics (but legally compliant) cybersecurity tool designed for human good. Its primary mission is to clean a user's digital footprint from the internet by finding exposed personal data and forcing its removal through automated, legally binding takedown requests.

This initial phase (MVP) focuses on building the **Core**, **Scanner**, **Takedown Enforcer**, and **Legal Engine**. The interface will be a Hacker-style CLI.

## Architecture

Kelp is divided into four main modular components:

### 1. The Vault (`profile.yaml`)
- **Purpose**: Securely stores the user's target data (names, emails, phone numbers, usernames, physical addresses).
- **Security**: Local-only storage. Data never leaves the machine except when explicitly injected into outbound legal emails or encrypted search queries.

### 2. The Scanner (`scanner.py`)
- **Purpose**: Hunts for the user's data across the open web.
- **Mechanisms**:
  - **Google Dorks**: Uses advanced search operators (e.g., `intext:"target_email" AND "password"`) to find exposed data.
  - **API Integrations**: Connects to public breach databases (e.g., HaveIBeenPwned) to identify compromised accounts.
- **Output**: A list of URLs and domains where the user's data is currently hosted.

### 3. The Takedown Enforcer (`takedown.py`)
- **Purpose**: Identifies the infrastructure behind the offending URLs.
- **Mechanisms**:
  - Runs automated `WHOIS` lookups and DNS resolution on target domains.
  - Identifies the hosting provider (e.g., AWS, Cloudflare, Namecheap).
  - Extracts the designated `abuse@` or legal contact email for that provider.

### 4. The Legal Engine (`legal.py`)
- **Purpose**: Drafts and sends aggressive, legally sound takedown notices.
- **Mechanisms**:
  - Uses `Jinja2` templating to generate contextual emails.
  - **Data Brokers**: Generates CCPA/GDPR "Right to be Forgotten" requests.
  - **Data Leaks**: Generates DMCA Takedown or Acceptable Use Policy (AUP) violation notices targeting the host.
  - Connects to the user's email provider via SMTP to automatically dispatch the requests.

## User Interface (CLI)
Built using Python's `Typer` and `Rich` libraries for a clean, hacker-aesthetic terminal experience.

**Key Commands**:
- `kelp init`: Generates the `profile.yaml` template.
- `kelp scan`: Runs the OSINT scanner and lists exposures.
- `kelp enforce`: Takes the scan results, performs WHOIS lookups, and dispatches the legal emails.
- `kelp status`: Tracks the status of sent requests.

## Data Flow
1. User populates `profile.yaml`.
2. User runs `kelp scan`. Scanner finds `sketchy-broker.com/profile/user`.
3. User runs `kelp enforce`.
4. Enforcer looks up `sketchy-broker.com`, finds it is hosted on Cloudflare.
5. Legal Engine generates a CCPA request and emails it to Cloudflare's abuse contact and the broker's privacy contact.
6. Local database logs the action to prevent duplicate emails.

## Future Expansion
This architecture is designed to easily integrate future modules:
- **Data Obfuscation / Poisoning Engine** (flooding databases with fake data).
- **Account Terminator** (Playwright-based automated account deletion).
