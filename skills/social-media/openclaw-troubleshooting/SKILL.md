---
name: openclaw-troubleshooting
description: OpenClaw 故障排查指南 — Gateway 启动、Telegram 频道配置、配对问题
triggers:
  - openclaw gateway 无法连接
  - openclaw pairing 失败
  - openclaw telegram 收不到消息
  - openclaw setup 配置丢失
category: social-media
---

# OpenClaw 故障排查

## 症状
- `openclaw pairing approve telegram <CODE>` 报错 "No pending pairing request found"
- Gateway 状态显示 "unreachable (connect failed: ECONNREFUSED 127.0.0.1:18789)"
- Telegram 突然无法接收消息
- Channels 列表为空

## 诊断步骤

### 1. 检查 Gateway 状态
```bash
openclaw status
```
重点看：
- `Gateway` 行是否显示 `reachable`
- `Channels` 行是否有 telegram 配置

### 2. 检查 Gateway 是否在运行
```bash
openclaw gateway status
```

### 3. 常见问题 A：Gateway 未安装 LaunchAgent

症状：`Gateway service: LaunchAgent not installed`，且 `openclaw gateway probe` 失败

**解决方法 — 设置 gateway.mode 并手动启动：**
```bash
# 设置本地模式
openclaw config set gateway.mode local

# 启动 Gateway（前台运行，观察日志）
openclaw gateway

# 或后台运行
openclaw gateway &
```

### 4. 常见问题 B：配置丢失（运行 openclaw setup 后）

症状：运行 `openclaw setup` 后，Telegram 频道配置消失，Channels 为空

**原因：** `openclaw setup` 会**覆盖** `~/.openclaw/openclaw.json`，不会合并配置

**解决方法 — 重新添加 Telegram 频道：**
```bash
openclaw channels add --channel telegram --token "你的BOT_TOKEN"
```

**预防：** 运行 `openclaw setup` 前先备份配置
```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup
```

### 5. 常见问题 C：配对码无效

症状：`No pending pairing request found for code: XXXXXX`

**可能原因：**
1. Telegram 频道未配置（最常见）— 先添加频道
2. 配对码已过期
3. 配对请求来自其他 OpenClaw 实例

**解决步骤：**
```bash
# 确认 Telegram 频道已配置
openclaw channels list

# 如果为空，重新添加
openclaw channels add --channel telegram --token "BOT_TOKEN"

# 然后让对方重新获取配对码
```

### 6. 检查日志
```bash
# Gateway 日志
openclaw logs --limit 50

# 检查后台进程
openclaw status
```

## 关键命令速查

| 任务 | 命令 |
|------|------|
| 查看状态 | `openclaw status` |
| 启动 Gateway | `openclaw gateway` |
| 设置本地模式 | `openclaw config set gateway.mode local` |
| 查看频道列表 | `openclaw channels list` |
| 添加 Telegram | `openclaw channels add --channel telegram --token "TOKEN"` |
| 查看待处理配对 | `openclaw pairing list telegram` |
| 批准配对 | `openclaw pairing approve telegram <CODE>` |
| 备份配置 | `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak` |

### 7. 常见问题 D：CLI 损坏（npm install 被中断）

症状：`openclaw` 命令报错 `Cannot find module '@exodus/bytes/encoding.js'` 或其他模块缺失

**原因：** 使用 `npm install` 或 `npm update` 时被中断，导致 `node_modules` 不完整

**解决方法 — 完整重装 openclaw：**
```bash
# 1. 删除损坏的 openclaw
rm -rf ~/.nvm/versions/node/v22.15.0/lib/node_modules/openclaw

# 2. 重新安装
cd ~/.nvm/versions/node/v22.15.0/lib/node_modules
npm install openclaw --legacy-peer-deps
```

### 8. 常见问题 E：Telegram 网络连接失败

症状：日志显示 `Network request for 'deleteMyCommands' failed!`、`SSL_ERROR_SYSCALL`、`httpx.ConnectError`，或 Gateway 发送消息“没反应”但没有明确业务报错。

**先区分两类情况：**
1. **整机网络不通**：连 `api.telegram.org` 都访问不到
2. **只有 Python/Gateway 不通**：`curl` 能通，但 Hermes/OpenClaw 的 Python/httpx 请求失败

**诊断：**
```bash
# 1) 先看基础网络是否通
curl -I -v https://api.telegram.org

# 2) 再用与 Gateway 同一套 Python 直接测 Bot API
source ~/.hermes/.env 2>/dev/null || true
/Users/$USER/.hermes/hermes-agent/venv/bin/python - <<'PY'
import os, json, urllib.request, ssl
from urllib.error import URLError, HTTPError

token = os.environ.get('TELEGRAM_BOT_TOKEN')
url = f'https://api.telegram.org/bot{token}/getMe'
try:
    with urllib.request.urlopen(url, timeout=20, context=ssl.create_default_context()) as r:
        print(r.status)
        print(json.loads(r.read().decode('utf-8', 'replace')).get('ok'))
except HTTPError as e:
    print('HTTP_ERROR', e.code)
    print(e.read().decode('utf-8', 'replace')[:300])
except URLError as e:
    print('URL_ERROR', repr(e.reason))
except Exception as e:
    print(type(e).__name__, str(e))
PY
```

**如果出现这种组合：**
- `curl https://api.telegram.org` 成功
- 但 Python/Gateway 报 `SSLCertVerificationError: self-signed certificate in certificate chain`
- 或报 `SSLEOFError: UNEXPECTED_EOF_WHILE_READING`
- 或 Gateway 日志只写 `telegram.error.NetworkError: httpx.ConnectError`

那么重点不是 token/chat_id，而是：
**本机 Python TLS/证书链与当前网络出口不兼容**。

**可能原因：**
1. 企业网络 / VPN / 安全软件 / 抓包代理注入了中间证书
2. Python 使用的 CA 证书链不信任当前链路返回的证书
3. 系统浏览器/curl 能通，但 Python 的 OpenSSL/httpx 校验失败
4. 某些出口对 Python TLS 握手不稳定，导致 EOF/握手中断

**进一步检查：**
```bash
# 看是否设置了代理/证书相关环境变量
env | egrep '^(HTTP_PROXY|HTTPS_PROXY|ALL_PROXY|NO_PROXY|SSL_CERT_FILE|REQUESTS_CA_BUNDLE|CURL_CA_BUNDLE|PYTHONHTTPSVERIFY|NODE_TLS_REJECT_UNAUTHORIZED)='

# 看 Python 默认 CA 路径
python3 - <<'PY'
import ssl
print(ssl.get_default_verify_paths())
PY
```

**解决：**
- 先确认是不是代理/VPN/安全软件导致的 HTTPS 拦截
- 如需代理，在配置中为 Gateway 使用正确代理
- 如是企业自签证书链，需把受信任 CA 导入 Python/OpenSSL 可见的证书链
- 重启 Gateway 后重新验证 `getMe` / `sendMessage`
- 不要只看 `curl`；必须用 Gateway 同一套 Python 再测一次

**经验结论：**
当 Gateway 发 Telegram “没反应”时，若日志是 `httpx.ConnectError`，且 `curl` 正常，不要先怀疑 bot 逻辑；优先排查 Python TLS 证书链问题。

### 9. 常见问题 F：配置第三方 API（MiniMax/Custom OpenAI-Compatible）

症状：`Missing API key for OpenAI` 或类似错误

**错误尝试：**
```bash
# 以下方式无效 — openclaw.json 不支持 providers 作为根键
openclaw config set providers.openai-compatible.xxx  # 会报错 Unrecognized key
```

**正确方法 — 通过环境变量传递：**
```bash
# 启动 Gateway 时设置环境变量
OPENAI_API_KEY="你的API_KEY" \
OPENAI_BASE_URL="https://api.minimaxi.com/anthropic/v1" \
openclaw gateway &

# 或一行
OPENAI_API_KEY="sk-xxx" OPENAI_BASE_URL="https://xxx.anthropic.com/v1" openclaw gateway
```

**注意：**
- `providers` 不是有效的根级配置键，会报错 `Unrecognized key: providers`
- API Key 必须通过环境变量传递给 Gateway 进程
- 重启 Gateway 后环境变量需要重新设置

### 10. 常见问题 G：Gateway 重启后配置丢失

症状：重启 Gateway 后 Telegram 又显示未配置

**原因：** 环境变量没有持久化，每次启动都需要重新设置

**解决：** 使用 launchd 服务持久化，或创建启动脚本

症状：日志显示 `Network request for 'deleteMyCommands' failed!` 或 `SSL_ERROR_SYSCALL`

**诊断：**
```bash
curl -v https://api.telegram.org
```

**可能原因：**
1. 网络无法访问 Telegram API（企业网络/防火墙/代理）
2. 在中国地区需要配置代理
3. SSL 证书被拦截

**解决：**
- 检查网络能否访问 Telegram
- 如需代理，在 `openclaw.json` 中配置代理
- 或使用 VPN/代理确保能连接到 `api.telegram.org:443`

## 重要注意事项

1. **不要随意运行 `openclaw setup`** — 会覆盖现有配置
2. **Gateway 需要 `gateway.mode=local`** — 否则启动被阻止
3. **配置丢失后需要重新添加频道** — Telegram token 需要重新输入
4. **npm install 被中断会导致 CLI 损坏** — 需要完整重装
5. **Telegram 报错 Network request failed = 网络不通** — 先检查网络
6. **第三方 API（如 MiniMax）不能用 openclaw.json 配置 providers** — 必须通过环境变量
7. **每次重启 Gateway 都需要重新设置环境变量** — 使用 launchd 服务持久化
