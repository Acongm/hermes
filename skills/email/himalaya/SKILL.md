---
name: himalaya
description: CLI to manage emails via IMAP/SMTP. Use himalaya to list, read, write, reply, forward, search, and organize emails from the terminal. Supports multiple accounts and message composition with MML (MIME Meta Language).
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

For Himalaya v1.2.x, configure an existing account name with:

```bash
himalaya account configure <account>
```

Or create `~/.config/himalaya/config.toml` manually.

### Important: Himalaya v1.2 config shape

Himalaya v1.2 uses account tables under `[accounts.<name>]`.
Do **not** use legacy top-level keys like `default = "personal"` from older docs — they can fail to parse.

Minimal working example:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"

folder.aliases.inbox = "INBOX"

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring
# backend.auth.raw = "app-password-or-imap-password"  # acceptable for quick testing only

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"
# message.send.backend.auth.raw = "smtp-password"
```

For Gmail app passwords, SMTP 465 + `tls` is also common and works with official examples.

### Useful v1.2 command notes

- List accounts:

```bash
himalaya account list
```

- Diagnose one account:

```bash
himalaya account doctor personal
```

- Select account for commands with `-a <name>` on the subcommand, for example:

```bash
himalaya envelope list -a personal -f INBOX
himalaya message read -a personal 42
```

Do **not** assume the old top-level `--account` placement still works the same across examples; prefer the documented per-subcommand `-a/--account` flag.

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input (`cat << EOF | himalaya template send`) is recommended for reliability. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — pipe the message via stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder:

```bash
himalaya message move 42 "Archive"
```

Copy to folder:

```bash
himalaya message copy 42 "Important"
```

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

List accounts:

```bash
himalaya account list
```

Use a specific account:

```bash
himalaya --account work envelope list
```

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## 126 Mail / NetEase Pitfall

For `@126.com` / NetEase mailboxes, having an IMAP/SMTP authorization code is sometimes **not sufficient**.

A common failure mode is:

- IMAP `LOGIN` succeeds
- but `SELECT INBOX` fails with:
  - `SELECT Unsafe Login. Please contact kefu@188.com for help`

This means the server accepted credentials but still blocked mailbox access as a risky login.

### What to check

1. Confirm IMAP is enabled in the 126 mailbox web settings.
2. Confirm the authorization code is current (not revoked/regenerated).
3. Check 126/NetEase account security controls for:
   - third-party client login restrictions
   - unusual login protection / device protection
   - IMAP client allowlist or verification prompts
4. If Hermes/Python can `LOGIN` but cannot `SELECT`, do **not** assume the password is wrong — treat it as a provider-side security block.

### Useful low-level verification

```bash
python3 - <<'PY'
import imaplib
mail=imaplib.IMAP4_SSL('imap.126.com', 993)
print('login', mail.login('you@126.com', 'AUTH_CODE'))
print('select', mail.select('INBOX'))
mail.logout()
PY
```

Interpretation:
- `LOGIN completed` + `SELECT Unsafe Login` => credentials work, mailbox access is still blocked by provider policy.
- `LOGIN failed` => wrong auth code or IMAP not enabled.

### Hermes guidance

When this happens, tell the user explicitly that:
- the mailbox did not fully reject the credential,
- 126 is blocking the session as unsafe,
- they may need to approve/relax the login in 126 web security settings before Himalaya will work.

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## NetEase 126/163 special pitfall: `Unsafe Login`

NetEase IMAP can behave in a surprising way:
- `LOGIN` succeeds
- basic commands like `NOOP` / `STATUS INBOX (MESSAGES)` may succeed
- but `SELECT INBOX` fails with:

```text
SELECT Unsafe Login. Please contact kefu@188.com for help
```

This can happen **even when IMAP is enabled and the authorization code is correct**.

### What this usually means

NetEase expects the client to send the IMAP `ID` extension (RFC 2971) before selecting the mailbox.
Some third-party libraries/clients do not send it, and NetEase flags the session as unsafe.

### Practical implications for Hermes

- If `himalaya account doctor` says IMAP/SMTP are OK but mailbox listing still fails on NetEase with `Unsafe Login`, the issue may be **client identification**, not the password.
- Also check the mailbox itself for a security notice like `新设备登录提醒` / blocked receive behavior after testing.

### Recommended handling

1. First verify the obvious things anyway:
   - IMAP is enabled in the web UI
   - authorization code is correct
2. If login works but `SELECT INBOX` fails with `Unsafe Login`, suspect missing IMAP `ID`
3. If Himalaya cannot work around it, use a lower-level IMAP path that sends `ID` before `SELECT`
4. Explain clearly to the user that this is a NetEase-specific server policy / compatibility issue, not necessarily a bad password

### Useful diagnostic pattern

A lower-level IMAP probe can reveal this exact behavior:
- `LOGIN` → OK
- `NOOP` / `STATUS` → OK
- `SELECT INBOX` → `Unsafe Login`

That pattern is a strong sign the auth is valid but the session is being blocked by NetEase policy.

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`).
- Store passwords securely using `pass`, system keyring, or a command that outputs the password.
