# hermes

Personal Hermes configuration and a mirrored snapshot of the local Hermes skills catalog used on this machine.

## Contents
- `config/config.public.yaml` — sanitized Hermes config snapshot
- `config/SOUL.md` — exported agent persona/config notes
- `config/email_accounts.example.json` — example multi-account config via env var
- `skills/` — mirrored `~/.hermes/skills/` tree from this machine
- `skills/email/generic-email-daily-summary/` — custom multi-account email summary skill
- `skills/email/generic-email-daily-summary/scripts/email_summary_last24h.py` — generic multi-account IMAP summary script

## Sync policy
This repo is used to back up skills that Hermes harness can use or has used on this machine.
The `skills/` directory is synced from the local `~/.hermes/skills/` tree.

## Secrets
Do not commit real passwords, tokens, or app-specific passwords.
Use environment variables instead.

Recommended local env vars:
- `HERMES_EMAIL_ACCOUNTS_JSON`
- `HERMES_EMAIL_126_APP_PASSWORD`
- `HERMES_EMAIL_GMAIL_APP_PASSWORD`
