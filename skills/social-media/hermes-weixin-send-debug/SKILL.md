---
name: hermes-weixin-send-debug
description: Diagnose Hermes Weixin send failures, especially duplicate token-lock conflicts and recipient identification issues
triggers:
  - Hermes 微信发不出去
  - Weixin bot token already in use
  - 想单独测试微信发送但主 gateway 已在运行
  - 只有微信号/备注名，没有 chat_id
category: social-media
---

# Hermes Weixin 发送排查

适用场景：
- 用户要你“用微信发消息”
- 想验证 WeixinAdapter 能否发送
- 手动测试时报 `Weixin bot token already in use`
- 用户给的是微信号/备注名截图，而不是 Hermes 可直接发送的 `chat_id`

## 关键结论

1. `WEIXIN_TOKEN` 同一时间只能被一个 Hermes gateway/adapter 实例占用。
2. 如果主 gateway 已经在线，再启动一个独立 Python/adapter 测试进程，常见报错是：
   - `[Weixin] Weixin bot token already in use (PID XXXX). Stop the other gateway first.`
3. 这类报错表示“重复占用发送通道”，不等于“微信本身无法发送”。
4. 用户提供的微信资料页截图（如备注名、昵称、微信号）通常不足以直接发送；Hermes 发送更可靠的是 `chat_id`（常见形如 `...@im.wechat`）或已建立过上下文 token 的聊天对象。

## 先做的检查

### 1. 看 gateway 状态
```bash
python3 - <<'PY'
from pathlib import Path
p=Path.home()/'.hermes'/'gateway_state.json'
print(p)
print('exists', p.exists())
if p.exists():
    print(p.read_text()[:4000])
PY
```

重点看：
- `platforms.weixin.state`
- 是否已有 Hermes gateway 在运行

### 2. 看是否已有 Weixin 上下文 token
```bash
python3 - <<'PY'
from pathlib import Path
p=Path.home()/'.hermes'/'weixin'/'accounts'
print(p)
for f in p.glob('*.context-tokens.json'):
    print('\nFILE:', f)
    print(f.read_text())
PY
```

说明：
- `~/.hermes/weixin/accounts/<account_id>.context-tokens.json` 里记录的是可直接回复过的聊天对象及其 `context_token`
- 如果目标联系人不在这里，直接发信成功率会低，通常还缺少 Hermes 侧可用的收件标识

### 3. 搜索本地是否已有目标 chat_id
```bash
# 例：已知昵称/微信号时
search_files pattern="shenan975|Arong|妹妹|im\\.wechat" path="~/.hermes" target="content"
```

## 如何解释“token already in use”

当你用独立脚本直接构造 `WeixinAdapter` 测试发送时，例如：
```python
adapter = WeixinAdapter(PlatformConfig(enabled=True))
await adapter.connect()
```
如果主 gateway 已持有同一个 `WEIXIN_TOKEN`，`connect()` 会失败。

这时应该告诉用户：
- 当前微信通道其实已经连着
- 失败的是“第二个测试进程”
- 不是已经证明“微信发不出去”

## 正确处理顺序

### 场景 A：主 gateway 正在运行
优先结论：不要再开第二个 adapter 抢 token。

应做：
1. 确认主 gateway 的 weixin 平台是 `connected`
2. 确认是否已有目标 `chat_id` / `@im.wechat` 标识
3. 如果只有微信号、昵称、截图，没有 Hermes chat_id，就先向用户解释“还缺可发送目标”
4. 若用户只是要发到已绑定的 home channel，可直接用该 home channel

### 场景 B：需要离线单测 adapter
只有在你明确要停掉主 gateway 时，才可单独测试：
1. 停掉正在运行的 gateway
2. 再启动独立 adapter 测试
3. 测完恢复主 gateway

除非用户明确要求，不要为了单测去中断现有 gateway。

## 关于联系人标识的经验规则

不要把这些当成可直接发送目标：
- 微信资料页里的“微信号” (`shenan975` 这类)
- 备注名（如“妹妹”）
- 昵称（如 `Arong`）

优先使用这些：
- Hermes 已知 `chat_id`
- `WEIXIN_HOME_CHANNEL`
- `*.context-tokens.json` 里已有的 `@im.wechat` 对象
- 日志中出现过的 inbound `from=...@im.wechat`

### 新增实测结论：微信号直发通常会失败

如果你把资料页里的“微信号”直接当 `to_user_id` 去调 iLink 接口，常见现象是：

1. `getconfig` 返回：
```json
{"ret":-4,"errmsg":"GetTypingTicket rpc failed"}
```

2. `sendmessage` 返回：
```json
{"ret":-3}
```

经验解释：
- 这通常不是“网络坏了”
- 而是目标标识不被当前 iLink/Hermes 发送接口识别
- 换句话说，微信资料页里的微信号 ≠ Hermes 可直接发送的收件 `chat_id`

因此，当用户说“我只有微信号，没有别的 ID”时，应明确说明：
- 当前微信通道可能是在线的
- 但仅凭微信号无法确认可发
- 需要真实的 Hermes chat_id / 已建立上下文的对象 / Home channel 才能稳定发送

## 典型对外说明模板

- “现在报错不是微信本身发送失败，而是同一个微信 token 已被正在运行的主 gateway 占用；我刚才那次只是独立测试进程抢不到连接。”
- “你给我的截图能确认联系人是‘妹妹 / Arong / 微信号 shenan975’，但这还不是 Hermes 可直接发送的 chat_id；如果你给我对应的 `@im.wechat` 目标或让我发到已绑定 Home 频道，我就能继续。”

## 客户端自动化的补充判断（macOS）

如果用户要求“那就直接操作我本机微信客户端发送”，先区分两件事：

1. `tell application "WeChat" to activate` 成功
2. 但 `System Events` / `osascript` 读取前台窗口、读取 WeChat 窗口时长时间超时

这通常说明：
- 微信客户端存在且能被唤起
- 但终端 / osascript / System Events 没拿到足够的辅助功能（Accessibility）或自动化（Automation）权限
- 不是微信未登录，也不是脚本路径错误

对用户的建议：
- 去“系统设置 → 隐私与安全性 → 辅助功能 / 自动化”放行 Terminal 或 iTerm、WeChat、System Events
- 改完后要彻底退出并重开 WeChat 和终端；仅仅勾选权限后不重开，AppleScript 常常仍然超时

## 常见坑

1. 不要把“token already in use”误判成“微信不能发”。
2. 不要因为验证发送而随便停掉用户正在运行的主 gateway。
3. 不要把微信号/备注名直接当成 Hermes 的 `chat_id`。
4. 如果主 gateway 已连接，优先沿用主 gateway 通道，而不是另起一个 adapter。
5. 在 macOS 上，`WeChat activate` 成功不代表你已经获得了 UI 自动化权限；真正的信号是 `System Events` 能否快速读到前台/窗口信息。
