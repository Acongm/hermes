---
name: smtp-debug-vpn
description: Diagnose and resolve SMTP email sending failures caused by VPN/proxy interference
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [email, smtp, vpn, proxy, network, debugging]
    related_skills: [himalaya]
---

# SMTP Debugging: VPN/Proxy Interference

When email sending fails with SSL errors or connection closed, VPN/proxy is often the cause.

## Key Symptoms

1. SMTP server resolves to `198.18.x.x` (VPN internal IP) instead of public IP
2. `smtplib.SMTP_SSL` fails with `UNEXPECTED_EOF_WHILE_READING`
3. `SMTPServerDisconnected: Connection unexpectedly closed`
4. `curl -v smtp://smtp.example.com:465` shows `Host ... was resolved` to a `198.18.x.x` address
5. `dig smtp.example.com` returns a `198.18.x.x` address

**Root cause**: DNS is hijacked by the VPN → VPN intercepts SSL connection → proxy terminates it mid-stream.

## Diagnosis Steps

```bash
# 1. Check proxy/VPN status
networksetup -getsecurewebproxy "Wi-Fi"
scutil --nwi | head -15

# 2. Test SMTP connectivity
curl -v --connect-timeout 5 --url "smtp://smtp.126.com:465" 2>&1

# 3. Check DNS resolution (if it returns 198.18.x.x, VPN is intercepting)
dig smtp.126.com
nslookup smtp.126.com

# 4. Check what's running on proxy port
lsof -i :7890
```

## Solution

The fix is NOT in the email configuration — it requires **proxy software configuration**:

1. **Add SMTP domains to the proxy bypass/whitelist**:
   - `smtp.126.com`, `smtp.gmail.com`, etc.
   - Or bypass entire port 465 and 587

2. **Restart the VPN/proxy** after making changes.

3. **Alternative**: Route email traffic through a VPN profile that doesn't intercept SMTP.

## Example: Quantumult X fix

If the machine is running **Quantumult X**, check its live config in:

```bash
~/Library/Group\ Containers/group.com.crossutility.quantumult-x/Documents/configuration/default.conf
```

Two changes may be required:

### 1) Disable placeholder-IP mapping for mail domains

Add the affected domains to `dns_exclusion_list` so Quantumult stops mapping them into `198.18.0.0/15` placeholder IPs:

```conf
dns_exclusion_list = *.cmpassport.com, *.jegotrip.com.cn, *.icitymobile.mobi, id6.me, *.126.com, *.mail.126.com, smtp.126.com, imap.126.com, pop.126.com
```

### 2) Force mail domains to DIRECT

Add explicit direct rules in the filter section:

```conf
HOST-SUFFIX,126.com,DIRECT
HOST,smtp.126.com,DIRECT
HOST,imap.126.com,DIRECT
HOST,pop.126.com,DIRECT
```

Then restart Quantumult X or reconnect its tunnel and retest SMTP.

## Example: Clash-based proxy bypass

In `~/.config/clash/config.yaml` or similar, add:

```yaml
rules:
  - DOMAIN-SUFFIX,126.com,DIRECT
  - DOMAIN-SUFFIX,gmail.com,DIRECT
  - DOMAIN-KEYWORD,smtp,DIRECT
```

## Note

Standard SMTP ports (465=SSL, 587=STARTTLS) are commonly blocked by corporate firewalls too. If bypassing the proxy doesn't work, also check if port 465/587 outbound is allowed.

## Verification guidance

- Do not rely only on `nslookup`/`dig` after the config change; some VPN tools may still show tunnel-side resolver behavior.
- The decisive test is an actual SMTP login/send attempt, e.g. with Python `smtplib`.
- If `smtplib.SMTP_SSL(...).login(...).send_message(...)` succeeds, treat the mail path as fixed even if DNS output still looks unusual.
