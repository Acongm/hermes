# hermes

Personal Hermes configuration, scripts, and reusable skills.

## Contents
- `config/config.public.yaml` — sanitized Hermes config snapshot
- `scripts/email_summary_last24h.py` — generic multi-account IMAP summary script
- `skills/email/generic-email-daily-summary/SKILL.md` — summary formatting skill
- `config/email_accounts.example.json` — example multi-account config via env var

## Secrets
Do not commit real passwords or app-specific passwords.
Use environment variables instead.

Recommended local env vars:
- `HERMES_EMAIL_ACCOUNTS_JSON`
- `HERMES_EMAIL_126_APP_PASSWORD`
- `HERMES_EMAIL_GMAIL_APP_PASSWORD`
