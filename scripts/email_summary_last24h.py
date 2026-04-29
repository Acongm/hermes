#!/usr/bin/env python3
import os, json, imaplib, email, email.header, datetime, re, ssl, time
from email.utils import parsedate_to_datetime
from pathlib import Path


def load_dotenv(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        os.environ.setdefault(k, v)


def dh(x):
    if not x:
        return ''
    out=[]
    for txt, enc in email.header.decode_header(x):
        if isinstance(txt, bytes):
            out.append(txt.decode(enc or 'utf-8', 'replace'))
        else:
            out.append(txt)
    return ''.join(out)


def extract_text(msg):
    body=''
    if msg.is_multipart():
        for part in msg.walk():
            ctype=part.get_content_type()
            disp=str(part.get('Content-Disposition',''))
            if 'attachment' in disp.lower():
                continue
            if ctype=='text/plain':
                payload=part.get_payload(decode=True)
                if payload is not None:
                    charset=part.get_content_charset() or 'utf-8'
                    body=payload.decode(charset,'replace')
                    break
        if not body:
            for part in msg.walk():
                if part.get_content_type()=='text/html':
                    payload=part.get_payload(decode=True)
                    if payload is not None:
                        charset=part.get_content_charset() or 'utf-8'
                        html=payload.decode(charset,'replace')
                        html=re.sub(r'<(script|style).*?</\\1>', ' ', html, flags=re.S|re.I)
                        html=re.sub(r'<[^>]+>', ' ', html)
                        body=html
                        break
    else:
        payload=msg.get_payload(decode=True)
        if payload is not None:
            charset=msg.get_content_charset() or 'utf-8'
            body=payload.decode(charset,'replace')
    return ' '.join(body.split())


def send_imap_id_if_needed(mail, account):
    if not account.get('imap_id_workaround'):
        return
    try:
        tag = mail._new_tag()
        name = account.get('imap_id_name', 'IMAPClient')
        version = account.get('imap_id_version', '2.1.0')
        vendor = account.get('imap_id_vendor', 'Hermes')
        contact = account.get('imap_id_contact', account.get('email',''))
        args = f'("name" "{name}" "version" "{version}" "vendor" "{vendor}" "contact" "{contact}")'
        mail.send(f'{tag} ID {args}\r\n'.encode())
        try:
            mail._command_complete('ID', tag)
        except Exception:
            pass
    except Exception:
        pass


def collect_account(account, window_start, window_end, local_tz):
    host = account['host']
    port = int(account.get('port', 993))
    user = account['email']
    password = os.environ.get(account['password_env'], '')
    if not password:
        return {'account': account.get('label', user), 'email': user, 'error': f'missing env {account["password_env"]}', 'count': 0, 'emails': []}
    mailbox = account.get('folder', 'INBOX')
    since = (window_start - datetime.timedelta(days=1)).strftime('%d-%b-%Y')
    last = None
    mail = None
    for _ in range(3):
        try:
            mail = imaplib.IMAP4_SSL(host, port, ssl_context=ssl.create_default_context())
            break
        except Exception as e:
            last = e
            time.sleep(2)
    if mail is None:
        return {'account': account.get('label', user), 'email': user, 'error': repr(last), 'count': 0, 'emails': []}
    try:
        mail.login(user, password)
        send_imap_id_if_needed(mail, account)
        mail.select(mailbox)
        status, data = mail.search(None, f'(SINCE {since})')
        ids = data[0].split() if data and data[0] else []
        emails = []
        for mid in ids:
            status, msg_data = mail.fetch(mid, '(RFC822)')
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            try:
                dt = parsedate_to_datetime(msg.get('Date',''))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=local_tz)
                dt_local = dt.astimezone(local_tz)
            except Exception:
                continue
            if not (window_start <= dt_local < window_end):
                continue
            body = extract_text(msg)
            emails.append({
                'account': account.get('label', user),
                'email': user,
                'date_local': dt_local.strftime('%Y-%m-%d %H:%M'),
                'from': dh(msg.get('From','')),
                'to': dh(msg.get('To','')),
                'subject': dh(msg.get('Subject','')),
                'preview': body[:800],
                'body_length': len(body),
            })
        return {'account': account.get('label', user), 'email': user, 'error': None, 'count': len(emails), 'emails': sorted(emails, key=lambda x: x['date_local'], reverse=True)}
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def main():
    load_dotenv(Path.home()/'.hermes/.env')
    local_tz = datetime.datetime.now().astimezone().tzinfo
    now = datetime.datetime.now(local_tz)
    window_end = now
    window_start = now - datetime.timedelta(hours=24)
    cfg_text = os.environ.get('HERMES_EMAIL_ACCOUNTS_JSON', '[]')
    try:
        accounts = json.loads(cfg_text)
    except Exception as e:
        print(json.dumps({'error': f'cannot parse HERMES_EMAIL_ACCOUNTS_JSON: {e}'}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    results = [collect_account(acct, window_start, window_end, local_tz) for acct in accounts]
    merged = []
    for r in results:
        merged.extend(r['emails'])
    merged.sort(key=lambda x: x['date_local'], reverse=True)
    print(json.dumps({
        'window': 'last_24_hours',
        'window_start': window_start.isoformat(),
        'window_end': window_end.isoformat(),
        'generated_at': now.isoformat(),
        'account_count': len(accounts),
        'accounts': results,
        'count': len(merged),
        'emails': merged,
    }, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
