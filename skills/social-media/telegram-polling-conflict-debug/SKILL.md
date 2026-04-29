---
name: telegram-polling-conflict-debug
description: 诊断 Telegram Bot 收不到消息的问题，特别是"polling conflict"错误
triggers:
  - tg 收不到消息
  - telegram not receiving messages
  - Conflict getUpdates request
  - telegram token rejected
category: social-media
---

# Telegram Polling Conflict 故障排查

## 症状
Telegram 收不到消息，错误日志出现：
```
Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
```

## 诊断步骤

### 1. 检查 gateway_state.json
```bash
cat ~/.hermes/gateway_state.json
```
看 `platforms.telegram.error_code` 是否为 `telegram_connect_error`

### 2. 检查运行中的进程
```bash
ps aux | grep -i "hermes\|gateway" | grep -v grep
```
看是否有 **多个 Hermes/Gateway 进程** 同时运行（不同 PID）

### 3. 检查错误日志
```bash
grep -i "telegram\|token\|PCH6M87H" ~/.hermes/logs/gateway.error.log | tail -30
```
找 `Conflict` 和 `token rejected` 相关错误

### 4. 检查 Telegram Bot Token
确认 `.env` 或 `auth.json` 中的 `TELEGRAM_BOT_TOKEN` 是否正确、是否被注释。

**不要只看本地配置，直接用 Telegram API 验证 token：**
```bash
TOKEN='你的bot token'
curl -sk "https://api.telegram.org/bot$TOKEN/getMe"
```

结果判断：
- 返回 `{"ok":true,...}` → token 有效
- 返回 `401 Unauthorized` → token 已失效、被撤销或填错

如果用户刚在 @BotFather 里重置了 token，必须把新 token 写回 `~/.hermes/.env` 后重启 gateway。

### 5. 更新 token 后重启并验证
```bash
hermes gateway restart
```

**重要：仅修改 `~/.hermes/.env` 不够。**
运行中的 gateway 进程会继续使用旧环境变量；必须重启后新 token 才真正生效。

然后再次检查：
```bash
curl -sk "https://api.telegram.org/bot$TOKEN/getMyCommands"
```
如果能返回命令列表，通常说明 bot 已经成功连上。

**补充验证：主动发一条测试消息给自己的 chat_id**
```bash
curl -sk -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
  -d chat_id="你的Telegram用户ID" \
  --data-urlencode text="test from bot"
```
若 `sendMessage` 成功，则至少 bot→用户私聊发送链路正常。

### 6. 不要被旧状态文件误导
`~/.hermes/gateway_state.json` 可能保留旧 token 的 `error_message`，即使 Telegram 已重新连上。

因此排查优先级建议是：
1. Telegram API `getMe`
2. 最新 `~/.hermes/logs/agent.log`
3. 实际收发测试
4. 最后才参考 `gateway_state.json`

### 7. 用日志确认是否已经完成端到端收发
如果用户说“我发了但没反应”，重点看这些日志关键字：

- `inbound message: platform=telegram ...`
- `response ready: platform=telegram ...`
- `Sending response ...`

如果这三类日志都出现，说明：
- Telegram 消息已经进入 Hermes
- Hermes 已完成推理
- 回复已发回 Telegram

这时问题更可能在 Telegram 客户端显示延迟、看错会话，或用户没注意到短回复。

## 常见原因

1. **多个 Hermes 实例运行**（最常见）
   - Telegram 同一 Bot Token 只允许一个 polling 连接
   - 解决：杀掉重复进程，保留一个

2. **Bot Token 过期/被撤销**
   - 错误：`The token was rejected by the server`
   - 先不要猜，直接用 Telegram 官方 API 验证：
     ```bash
     curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
     ```
   - 如果返回：
     - `{"ok":true,...}` → token 本身有效，继续查 Hermes / 进程 / allowlist
     - `401 Unauthorized` → token 无效、已撤销、填错，必须去 @BotFather 生成新 token
   - 解决流程：
     1. 在 @BotFather 生成新 token
     2. 更新 `~/.hermes/.env` 里的 `TELEGRAM_BOT_TOKEN`
     3. `hermes gateway restart`
   - 经验结论：**只重置 token 不够**，如果没更新 `.env` 或没重启 gateway，运行中的 Hermes 仍会继续使用旧 token
   - 注意：`gateway_state.json` 可能残留旧 token 的历史报错文本；不要只看这个文件，要结合 `getMe` 和最新日志判断

3. **网络问题导致连接 Telegram 服务器失败**
   - 错误：`api.telegram.org connection failed`
   - 解决：检查网络/代理设置

### 补充：关闭系统代理软件（Clash/Quantumult X 等）

如果 Telegram 连接失败且发现 DNS 被劫持到 198.18.x.x，说明有代理软件在做 DNS 劫持。需要彻底关闭代理软件。

**Clash 通过 LaunchDaemon 管理，单独 kill 进程会被 launchd 自动重启：**

```bash
# 1. 找到 Clash 的 launchd plist
grep -r "clash" /Library/LaunchDaemons/

# 2. 卸载并停止（需要 sudo）
sudo launchctl unload /Library/LaunchDaemons/com.lbyczf.cfw.helper.plist
sudo launchctl stop /Library/LaunchDaemons/com.lbyczf.cfw.helper.plist

# 3. 如果 launchd 仍阻止，删除 plist 再 bootout
sudo rm /Library/LaunchDaemons/com.lbyczf.cfw.helper.plist
sudo launchctl bootout system/com.lbyczf.cfw.helper

# 4. 确认 Clash 进程已消失
ps aux | grep -i "clash" | grep -v grep
```

**Quantumult X** 用户：在 Quantumult X 设置中关闭相关代理规则。

### 杀重复进程操作
```bash
# 查看所有 hermes 相关进程
ps aux | grep -i "hermes\|gateway" | grep -v grep

# 杀掉指定的旧进程（保留最新的）
kill <PID>

# 确认只剩一个
ps aux | grep -i "hermes\|gateway" | grep -v grep
```

## 多账号 / 多 Bot 经验补充

### 同一个实例不能同时挂两个 Telegram Bot
当前 Hermes 这一套配置读取的是单个环境变量：
```bash
TELEGRAM_BOT_TOKEN
```
这意味着：
- 同一个实例一次只能服务 **一个** Telegram bot
- 如果把 `.env` 里的 token 改成另一个 bot 的 token，本质上是**切换 bot**，不是新增第二个 bot
- 如果想两个 bot 同时在线，需要跑第二个独立实例（独立配置目录 + 独立 gateway）

### 如果只是想让另一个 Telegram 人类账号也能用当前 bot
不要换 bot token，要做的是：
- 让对方先给 bot 发消息
- 获取对方 Telegram user ID，或直接让对方触发 pairing
- 批准 pairing：
```bash
hermes pairing approve telegram <CODE>
```
- 并确认 `TELEGRAM_ALLOWED_USERS` 包含该用户，例如：
```bash
TELEGRAM_ALLOWED_USERS=<your_user_id>,<their_user_id>
```
- 然后重启：
```bash
hermes gateway restart
```

## 验证修复
重启 Hermes Gateway 后，检查：
```bash
# 确认进程稳定运行
ps aux | grep -i hermes | grep -v grep

# 查看最新日志确认 Telegram connected
tail -20 ~/.hermes/logs/agent.log
```
