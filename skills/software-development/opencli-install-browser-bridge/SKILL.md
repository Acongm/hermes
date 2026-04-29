---
name: opencli-install-browser-bridge
description: Install OpenCLI on macOS/Linux, verify the daemon, and connect the Chrome Browser Bridge extension so local logged-in browser sessions can be reused.
triggers:
  - User wants to use OpenCLI to drive their real local browser or desktop apps
  - OpenCLI doctor says the extension is not connected
  - You need a safer alternative to remote browser sessions for logged-in sites like X/Twitter
---

# OpenCLI install + Browser Bridge connection

Use this when you want OpenCLI available locally and need it to reuse the user's real Chrome session.

## What mattered in practice

Installing the npm package is only half the job.
A successful `npm install -g @jackwener/opencli` can still leave OpenCLI unusable for browser control until the Chrome extension is installed and connected.

The decisive health check is:
```bash
opencli doctor
```

A common state is:
- daemon running
- extension not connected
- connectivity failed

That means the CLI is installed, but browser automation through the logged-in local browser still will not work.

## Requirements

From upstream docs:
- Node.js >= 21
- Chrome/Chromium available
- For browser commands, the Browser Bridge extension must be installed

## Install workflow

1. Verify runtime versions first:
```bash
node -v
npm -v
python3 --version
uname -a
```

2. Install OpenCLI globally:
```bash
npm install -g @jackwener/opencli
```

3. Verify the binary works:
```bash
opencli --version
opencli list
```

4. Run doctor immediately:
```bash
opencli doctor
```

Interpretation:
- If doctor shows daemon running but extension missing, do not pretend browser reuse is ready.
- The next step is extension installation, not more CLI retries.

## Browser Bridge extension setup

For OpenCLI v1.7.6, the latest GitHub release exposed this asset:
- `opencli-extension-v1.0.2.zip`

Programmatic way to discover the latest asset:
```bash
python3 - <<'PY'
import json, urllib.request
url='https://api.github.com/repos/jackwener/OpenCLI/releases/latest'
req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as r:
    data=json.load(r)
print(data['tag_name'])
for a in data.get('assets', []):
    print(a['name'], a['browser_download_url'])
PY
```

Download and extract:
```bash
python3 - <<'PY'
import urllib.request, os, zipfile
url='https://github.com/jackwener/OpenCLI/releases/download/v1.7.6/opencli-extension-v1.0.2.zip'
out='/tmp/opencli-extension-v1.0.2.zip'
urllib.request.urlretrieve(url, out)
extract='/tmp/opencli-extension-v1.0.2'
os.makedirs(extract, exist_ok=True)
with zipfile.ZipFile(out) as z:
    z.extractall(extract)
print(extract)
PY
```

Then in Chrome:
1. Open `chrome://extensions`
2. Enable Developer Mode
3. Click `Load unpacked`
4. Select the extracted folder, e.g.:
   - `/tmp/opencli-extension-v1.0.2`

## Why prefer manual extension loading first

If the user already has an active Chrome session with important tabs/logins, manual `Load unpacked` is the safest path.
Avoid casually restarting Chrome, changing profiles, or forcing a fresh automation-specific instance unless the user explicitly wants that.

This matters especially when the goal is to reuse the user's current logged-in X/Twitter session for screenshot or feed tasks.

## Important background-session limitation on macOS

A remote Hermes/gateway session may be able to do all of these:
- install `@jackwener/opencli`
- download and unzip the extension
- open `chrome://extensions`
- toggle Developer Mode through page JS / AppleScript
- even launch Chrome with `--load-extension=/path/to/extension`

…and still fail to actually connect the Browser Bridge.

### What happened in practice

In a Telegram/gateway-driven macOS session, the agent could:
- run `opencli doctor`
- inspect the user's Chrome profile and tabs
- open `chrome://extensions/`
- trigger `Load unpacked`
- send native key events to try selecting the unpacked folder

But OpenCLI still reported:
- daemon running
- extension not connected

And AppKit showed the real blocker:
```bash
cat >/tmp/front.swift <<'SWIFT'
import Foundation
import AppKit
let app = NSWorkspace.shared.frontmostApplication
print(app?.localizedName ?? "nil")
print(app?.bundleIdentifier ?? "nil")
SWIFT
swift /tmp/front.swift
```

If this returns something like:
- `loginwindow`
- `com.apple.loginwindow`

then the automation process is not attached to the user's real visible foreground desktop session.

### Interpretation

In that state:
- AppleScript may still read Chrome tabs and execute page JS
- `chrome://extensions` may still be scriptable enough to toggle Dev Mode
- but the final native file-picker / GUI confirmation path for `Load unpacked` is not trustworthy
- and `--load-extension=...` on a relaunched Chrome process may still fail to produce an actual daemon connection

So do **not** assume that “I can open the extensions page” means “I can finish extension install.”

### Practical rule

Before spending too long forcing GUI automation, verify whether the host process is really in the foreground GUI session.
On macOS, a quick AppKit check is often decisive.

If frontmost app resolves to `loginwindow`, treat the session as GUI-isolated and stop promising full self-service extension installation.

## Verification after extension load

Re-run:
```bash
opencli doctor
```

Expected improvement:
- daemon running
- extension connected
- connectivity OK

Then inspect available browser primitives:
```bash
opencli browser --help
```

Useful commands include:
- `opencli browser open <url>`
- `opencli browser state`
- `opencli browser screenshot [path]`
- `opencli browser eval <js>`
- `opencli browser click <target>`
- `opencli browser type <target> <text>`

## Practical notes

- `npm install -g` may emit engine warnings and still produce a working OpenCLI install. Treat those as secondary unless the binary itself fails.
- Do not confuse `opencli installed` with `OpenCLI browser-ready`.
- For local-browser tasks, `opencli doctor` is the source of truth.

## When to stop and ask the user

Stop after preparing the unpacked extension if the remaining step would modify the user's live Chrome setup.
At that point, ask the user to load the unpacked extension or explicitly approve using a separate Chrome instance/profile.

Also stop if your macOS session is GUI-isolated.
Signs include:
- `NSWorkspace.shared.frontmostApplication` reports `loginwindow`
- `opencli doctor` stays at `extension not connected` after both `chrome://extensions` automation attempts and `--load-extension=...` relaunch attempts
- you can inspect Chrome but cannot reliably complete the native picker / confirmation flow

In that case, report clearly that the blocker is the background GUI context, not just OpenCLI itself.

## Reusable outcome

This workflow is especially useful when a remote browser session cannot reuse the user's real login state and the user wants a more faithful local-browser path for sites like X/Twitter.
