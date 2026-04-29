---
name: telegram-native-file-delivery
description: Telegram 原生消息/附件发送指南：区分文本、图片、语音、音频、视频、文档的正确投递方式，并在 MEDIA:/path 失败或降级为路径文本时使用 Telegram 原生接口兜底。
triggers:
  - Telegram 发文件失败
  - MEDIA path shows up as text in Telegram
  - Telegram only shows local file path
  - Telegram PDF attachment not delivered
  - 用户要我直接发附件，不要发路径
  - Telegram 语音/视频/图片/文档发送方式
version: 2.0.0
author: Hermes Agent
---

# Telegram 原生消息与附件发送指南

适用场景：
- 用户在 Telegram 上要求“直接发给我”，而不是显示本地路径
- 需要判断应该发成 文本 / 图片 / 语音气泡 / 音频文件 / 视频 / 文档
- `MEDIA:/absolute/path` 没有被正确转换成 Telegram 原生附件
- 想搞清楚 Hermes 当前 Telegram 网关到底支持哪些发送方式、有哪些坑

## 先说结论

Telegram 里常见发送方式应该这样区分：

1. 纯文字
   - 走 `send_message`
   - 适合普通回复、长文拆分、多段说明

2. 图片（照片样式）
   - 本地图片：`send_photo`
   - 远程图片 URL：`send_photo`
   - 适合 `.png .jpg .jpeg .webp .gif`

3. 语音气泡
   - 走 `send_voice`
   - 适合 `.ogg .opus`
   - 这是 Telegram 里那种点一下就播放的语音泡泡

4. 音频文件
   - 走 `send_audio`
   - 适合 `.mp3 .wav .m4a` 等
   - 这是“音频附件”，不是圆形语音泡泡

5. 视频
   - 走 `send_video`
   - 适合 `.mp4 .mov .avi .mkv .webm .3gp`

6. 文档 / 文件附件
   - 走 `send_document`
   - 适合 `.pdf .txt .zip .docx` 等所有“不是照片/语音/视频”的文件
   - 这是“真正附件”的关键接口

## 代码里已经确认到的事实

### 1. Telegram 适配器本身原生支持这些接口
在 `gateway/platforms/telegram.py` 中：
- 文本：`self._bot.send_message(...)`
- 语音：`self._bot.send_voice(...)`
- 音频：`self._bot.send_audio(...)`
- 图片：`self._bot.send_photo(...)`
- 文档：`self._bot.send_document(...)`
- 视频：`self._bot.send_video(...)`

也就是说：
Hermes 的 Telegram 适配器“能力上”并不只会发图片，它本来就支持文档、音频、视频、语音等原生消息类型。

### 2. 网关后处理会按扩展名路由
在 `gateway/run.py` 中，后处理逻辑会把文件按扩展名分发：
- 音频扩展 → `send_voice`
- 视频扩展 → `send_video`
- 图片扩展 → `send_image_file`
- 其他扩展 → `send_document`

所以只要文件真的进入了“媒体投递流水线”，Telegram 端理论上能发成正确类型。

### 3. 真正的坑在 `extract_media()` 正则
在 `gateway/platforms/base.py` 的 `extract_media()` 里，`MEDIA:/path` 当前正则主要显式照顾这些扩展名：
- 图片：png/jpg/jpeg/gif/webp
- 视频：mp4/mov/avi/mkv/webm
- 音频：ogg/opus/mp3/wav/m4a

这里没有把 `.pdf`、`.txt`、`.zip`、`.docx` 之类文档扩展纳入“显式扩展白名单”。

结果就是：
- `MEDIA:/tmp/file.pdf` 有机会无法被可靠提取进入媒体流水线
- 用户看到的就可能只是 `MEDIA:/tmp/file.pdf` 文本、或者一条本地路径、或者占位符

### 4. bare local file path 自动识别也不是万能的
`extract_local_files()` 主要自动识别：
- 图片
- 视频

它不负责把裸露的 `.pdf`、`.zip` 这类文档路径都自动抓出来。

所以：
- 裸写 `/tmp/x.pdf` 不可靠
- `MEDIA:/tmp/x.pdf` 也不一定可靠
- 文档类想“稳”，应该直接走 Telegram 文档接口兜底

## 对 Telegram 的正确心智模型

### A. 文本消息
用途：普通说明、总结、解释

发送方式：
- `send_message`

特点：
- 会自动分块
- 适合主说明文字
- 不能替代附件

### B. 图片消息
用途：截图、海报、封面图、照片

发送方式：
- URL 图片 → `send_photo`
- 本地图片 → `send_photo`

Telegram 体验：
- 直接显示成图片
- 不是“文件列表式附件”

### C. 语音消息
用途：像微信/Telegram 那样可直接点播的语音

发送方式：
- `.ogg` / `.opus` → `send_voice`

Telegram 体验：
- 语音气泡
- 最符合“给我发语音”的用户预期

注意：
- `.mp3` 不会变成语音泡泡
- `.mp3` 走的是音频附件

### D. 音频文件
用途：音乐、播客、MP3 文件

发送方式：
- `.mp3 .wav .m4a` → `send_audio`

Telegram 体验：
- 音频附件
- 不是语音气泡

### E. 视频消息
用途：讲解视频、屏幕录制、短片

发送方式：
- `.mp4 .mov .avi .mkv .webm .3gp` → `send_video`

Telegram 体验：
- 通常可内联播放

### F. 文档/附件
用途：PDF、TXT、ZIP、DOCX、其他下载文件

发送方式：
- `send_document`

Telegram 体验：
- 标准文件附件
- 这是“不要发路径，直接把文件发我”的正确实现

## 实战原则

### 原则 1：不要把“本地路径文本”当作完成
错误做法：
- 直接回复 `/tmp/foo.mp3`
- 直接回复 `MEDIA:/tmp/foo.pdf` 然后不验证
- 用户已经说“你发的是地址”后还继续发路径

正确做法：
- 需要附件时，确保真正走到了 Telegram 原生发送接口
- 如果用户反馈看到的是路径文本，立即切换 Telegram API 直传

### 原则 2：用户说“发语音”，优先发语音气泡
- 优先 `.ogg/.opus`
- 若当前生成的是 `.mp3`，那发送结果更可能是音频附件而不是语音泡泡

### 原则 3：用户说“发文件”，优先走文档接口
特别是：
- PDF
- TXT
- ZIP
- DOCX
- 其他非图片/非视频/非语音文件

### 原则 4：MEDIA:/path 不是 Telegram 的万能真理，只是 Hermes 的中间约定
`MEDIA:/path` 本身不是 Telegram API。
它只是 Hermes 网关后处理时识别附件的一种约定格式。
所以：
- 识别成功 → 会转成原生消息
- 识别失败 → 用户就可能看到原始路径文本

## 推荐决策树

### 情况 1：我要发普通文本
直接发文本即可。

### 情况 2：我要发图片
优先：
- 远程图 URL 或本地图 → 走图片发送

### 情况 3：我要发“语音”
优先：
- 生成 `.ogg` / `.opus`
- 再走 `send_voice`

### 情况 4：我要发 MP3
认知上要明确：
- 这是音频文件
- 不是 Telegram 语音泡泡
- 应走 `send_audio`

### 情况 5：我要发 PDF 或其他文档
不要依赖用户替我验证 `MEDIA:/path` 是否被识别。
优先使用：
- `send_document`
- 或 Telegram Bot API `sendDocument` 直传

### 情况 6：用户已经说“你又发地址了”
说明这次任务失败，不要继续用同一失败方法重试。
应该：
1. 承认发送方式不对
2. 改用 Telegram 原生接口
3. 再发真正附件

## 可靠兜底：直接调用 Telegram Bot API

当 Hermes 的 `MEDIA:` 流水线没有把文件正确变成附件时，直接用 Telegram API 最稳。

### 发送文档
```bash
set -a && source ~/.hermes/.env >/dev/null 2>&1 && set +a
curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
  -F chat_id=<chat_id> \
  -F document=@/absolute/path/to/file.pdf \
  -F caption='可选说明'
```

### 发送语音气泡
```bash
curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVoice" \
  -F chat_id=<chat_id> \
  -F voice=@/absolute/path/to/file.ogg \
  -F caption='可选说明'
```

### 发送音频文件
```bash
curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendAudio" \
  -F chat_id=<chat_id> \
  -F audio=@/absolute/path/to/file.mp3 \
  -F caption='可选说明'
```

### 发送视频
```bash
curl --http1.1 -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
  -F chat_id=<chat_id> \
  -F video=@/absolute/path/to/file.mp4 \
  -F supports_streaming=true \
  -F caption='可选说明'
```

### 新增注意：MP4 走 `sendDocument` 时，Telegram 可能把它显示成 GIF/动画样式
实战里有一个容易误解的现象：
- 明明上传的是 `.mp4`
- 但如果走了 `sendDocument`
- Telegram 返回里可能同时带有 `animation` 和 `document`
- 用户前端会把它显示成类似 GIF/动图，而不是普通视频气泡

这不代表你真的发成了 GIF 文件，而是 Telegram 把“短、无声、适合循环”的 MP4 当成 animation 展示。

因此视频发送经验应补充为：
1. 用户明确要“视频”时，优先 `sendVideo`
2. `sendVideo` 失败时，`sendDocument` 可以作为兜底交付文件
3. 但要提前预期：兜底后的 MP4 可能在 Telegram 里显示成 animation/GIF 样式
4. 如果用户对展示形态敏感，要在回复里明确说明：
   - 文件本体仍是 MP4
   - 只是 Telegram 前端把它按 animation 显示
5. 对用户要“看操作过程”的场景，若 `sendVideo` 超时而 `sendDocument` 成功，可接受先交付 animation 样式的 MP4 证据，再继续解释原因

### 发送图片
```bash
curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendPhoto" \
  -F chat_id=<chat_id> \
  -F photo=@/absolute/path/to/file.png \
  -F caption='可选说明'
```

## 成功验证标准
成功结果里应看到：
- `"ok": true`
- `"result"`
- 对应消息类型字段，例如：
  - `"document"`
  - `"voice"`
  - `"audio"`
  - `"video"`
  - `"photo"`

## 这次补充学到的三个实战坑

### 坑 1：Telegram 视频直传时，`curl` 可能很久不返回，但并不代表失败
对较大的 MP4，实战里出现过这些现象：
- `MEDIA:/path/to/file.mp4` 在 Telegram 里退化成路径文本
- 直接 `sendVideo` 时遇到 `curl: (16) Error in the HTTP2 framing layer`
- Python `requests` / PTB / httpx 在上传阶段报 `write timeout`、`ReadError`、`RemoteProtocolError`
- 但改成 `curl --http1.1 -v` 后，其实文件会慢速上传成功，只是服务端 `200 OK` 会明显滞后

因此视频发送的经验规则应补充为：
1. 用户明确要“直接发视频”时，不要再回复 `MEDIA:/...` 文本。
2. 直传 Telegram Bot API 时，优先使用 `curl --http1.1`，避免部分环境下的 HTTP/2 framing 问题。
3. 需要排障时，用 `curl --http1.1 -v` 看是否先收到 `HTTP/1.1 100 Continue`，再观察上传是否推进，最后等待 `HTTP/1.1 200 OK`。
4. 即使上传在 100% 后卡很久，也先别急着取消；Telegram 可能还在服务端处理。
5. 如果原视频较大或网络不稳，可先压缩再发，提高成功率。

建议的压缩命令：
```bash
ffmpeg -y -i input.mp4 \
  -vf "scale=480:-2" \
  -c:v libx264 -preset veryfast -crf 34 \
  -c:a aac -b:a 64k \
  -movflags +faststart output_480.mp4
```

### 坑 2：不要把“home chat”默认当成当前用户正在说话的 chat
在 Telegram 里，用户可能同时有：
- 当前私聊 chat
- home chat
- 其他历史会话 chat

如果用户说“没收到”，要优先怀疑是不是发错 chat_id，而不是先怀疑 Telegram 没送达。

实战里出现过：
- 媒体组成功发送了
- 但发到了“另一个历史 home chat”
- 当前用户实际对话 chat 是“当前私聊 chat”
- 结果用户当前窗口里完全看不到

因此，发原生 Telegram API 前应：
1. 从当前会话上下文拿 chat_id（如果平台已明确提供）
2. 或从 `~/.hermes/logs/agent.log` 中查最新 `inbound message: platform=telegram user=... chat=...`
3. 用户反馈“没收到”时，立即核对 chat_id 是否发错

不要默认把：
- home channel
- 上一次成功发送的 chat
- 另一个 Telegram 会话
当成当前投递目标。

### 坑 2：发视频时，`requests` / 默认 HTTP 客户端不一定稳，优先试 `curl --http1.1`
实战里出现过：
- 本地视频已正确下载
- `requests.post(... sendVideo ...)` 在上传阶段报 `write operation timed out`
- PTB/httpx 也可能报：
  - `RemoteProtocolError: Server disconnected without sending a response`
  - `ReadError`
- 但用 `curl --http1.1 -F video=@file.mp4 .../sendVideo` 最终成功

说明：
- 有些环境里 Telegram 视频上传对客户端/连接行为更敏感
- `curl --http1.1` 往往比自写 Python 上传更稳
- 上传完成后 Telegram 可能还要处理几十秒，不能过早误判失败

建议的视频直传顺序：
1. 先尝试：
```bash
curl --http1.1 -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
  -F chat_id=<chat_id> \
  -F video=@/absolute/path/to/file.mp4 \
  -F supports_streaming=true \
  -F caption='可选说明'
```
2. 如果文件太大或网络差，先压缩后再传
3. 若 `curl` 已把 body 全部上传完成，不要因为服务器响应慢就立刻判失败
4. 对小到中等视频，必要时可加 `-v` 看是否已经：
   - 收到 `HTTP/1.1 100 Continue`
   - 完整上传 multipart body
   - 最终返回 `{"ok":true,...}`

### 实战补充：视频可先压缩到更稳的 Telegram 直发规格
如果原视频原生发送不稳，可先转成较小 MP4，再走 `sendVideo`：
- 分辨率例如：`480x854` 或 `720x1280`
- H.264 + AAC
- `-movflags +faststart`

示例：
```bash
ffmpeg -y -i input.mp4 \
  -vf "scale=480:-2" \
  -c:v libx264 -preset veryfast -crf 34 \
  -c:a aac -b:a 64k \
  -movflags +faststart output_480.mp4
```

## 给未来自己的操作规范

实战里，Telegram `sendVideo` 比 `sendDocument` / `sendPhoto` 更容易遇到“上传完成前连接被中断”或“写超时”问题。

本次踩到的具体现象：
- 直接回复 `MEDIA:/tmp/foo.mp4` 又退化成路径文本
- 用 `requests.post(... files=...)` 发 `19MB` 视频时，报：
  - `TimeoutError: The write operation timed out`
- 用 python-telegram-bot / httpx 发 `8MB` 视频时，报：
  - `httpx.RemoteProtocolError: Server disconnected without sending a response`
  - `httpx.ReadError`
- 但改用 `curl --http1.1` 直传一个更小的压缩版视频后，最终成功

### 经验结论

1. `MEDIA:/path` 对视频也可能退化成路径文本，不能盲信
2. `sendVideo` 遇到不稳定网络时：
   - `curl --http1.1` 往往比默认 HTTP/2 更稳
3. 大视频如果持续在上传阶段断开：
   - 不要只重试同一个大文件
   - 优先压缩到更小尺寸再直发

### 推荐视频兜底顺序

1. 先尝试原生 `sendVideo`
2. 如果失败且用户反馈看到的是路径/没收到：
   - 立即改走 Telegram Bot API
3. Bot API 发送时优先：
   - `curl --http1.1 -F video=@... -F supports_streaming=true`
4. 如果仍出现写超时 / RemoteProtocolError / ReadError：
   - 把视频转成更小的直发版再试

### 一个已验证成功的视频压缩方案

把竖屏视频压到 `480` 宽，并降低码率：
```bash
ffmpeg -y -i /absolute/path/to/input.mp4 \
  -vf "scale=480:-2" \
  -c:v libx264 -preset veryfast -crf 34 \
  -c:a aac -b:a 64k \
  -movflags +faststart \
  /tmp/video_480.mp4
```

再用 HTTP/1.1 发：
```bash
curl --http1.1 -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
  -F chat_id=<chat_id> \
  -F video=@/tmp/video_480.mp4 \
  -F supports_streaming=true \
  -F caption='可选说明'
```

### 实战数据点

一次成功案例里：
- 原视频：约 `19.5MB`，`1080x1920`，约 `24s`
- 压缩后：约 `2.39MB`，`480x854`
- 使用：
  - `curl --http1.1`
  - `sendVideo`
  - `supports_streaming=true`
- 结果：返回 `"ok": true`，成功在当前 Telegram 对话收到原生视频

### 上传等待时间不要设得太短

即便只有几 MB，Telegram 也可能在“upload completely sent off”之后还要等较久才返回 JSON。
所以：
- 视频直发不要只给 `20s` 或 `30s` 级别超时
- 实操中 `80s+` 才收到成功返回并不罕见

## sendPhoto 的关键尺寸坑（新增）

Telegram Bot API 的 `sendPhoto` 不是“只要是图片都行”。
至少要注意这两个限制：

- 宽 + 高 不能超过 `10000`
- 宽高比不能超过 `20:1`

典型报错：
- `Bad Request: PHOTO_INVALID_DIMENSIONS`

实际排查中，一个长图尺寸为：
- `1980 x 9698`
- 宽高和：`11678`
- 长宽比约 `4.9:1`

它被 `sendPhoto` 拒绝，不是因为比例，而是因为：
- `1980 + 9698 > 10000`

### 处理策略

如果用户要“图片形式”展示，而不是文件附件：

1. 先检查尺寸
   - macOS 可用：
   ```bash
   sips -g pixelWidth -g pixelHeight /absolute/path/to/image.png
   ```

2. 如果超过 `10000` 总和但用户仍想直接在聊天里看图：
   - 方案 A：等比缩小到满足限制，再走 `sendPhoto`
   - 方案 B：把长图切成多张，再按图片发送

3. 如果用户接受文件形式：
   - 直接走 `sendDocument`

### 经验结论

- “高清长图”经常能作为 document 成功发送，但未必能作为 photo 成功发送。
- 用户如果明确想要聊天里的图片预览，不要默认 document 就算完成；应先判断是否需要缩放或切图。

## 长图切图 + 四宫格/相册发送（新增）

当用户要“分成几张图按顺序一次发给我”，推荐直接用 Telegram Bot API `sendMediaGroup` 发相册，而不是逐条散发。

### 一个已验证成功的做法：把竖向长图平均切成 4 段

原图示例：
- `1980 x 9698`

平均切法：
- 前三张高度 `2424`
- 最后一张高度 `2426`

可用 `ffmpeg`：
```bash
mkdir -p /tmp/grid4 && \
ffmpeg -y -i /absolute/path/to/long.png -vf "crop=iw:2424:0:0" /tmp/grid4/01.png && \
ffmpeg -y -i /absolute/path/to/long.png -vf "crop=iw:2424:0:2424" /tmp/grid4/02.png && \
ffmpeg -y -i /absolute/path/to/long.png -vf "crop=iw:2424:0:4848" /tmp/grid4/03.png && \
ffmpeg -y -i /absolute/path/to/long.png -vf "crop=iw:2426:0:7272" /tmp/grid4/04.png
```

然后验证输出尺寸：
```bash
sips -g pixelWidth -g pixelHeight /tmp/grid4/01.png /tmp/grid4/02.png /tmp/grid4/03.png /tmp/grid4/04.png
```

### 一次性按顺序发送 4 张图

```bash
curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMediaGroup" \
  -F chat_id=<chat_id> \
  -F media='[
    {"type":"photo","media":"attach://img1","caption":"四宫格，按顺序查看 1→4"},
    {"type":"photo","media":"attach://img2"},
    {"type":"photo","media":"attach://img3"},
    {"type":"photo","media":"attach://img4"}
  ]' \
  -F img1=@/tmp/grid4/01.png \
  -F img2=@/tmp/grid4/02.png \
  -F img3=@/tmp/grid4/03.png \
  -F img4=@/tmp/grid4/04.png
```

成功标志：
- 返回 `"ok": true`
- `result` 是 4 条消息
- 它们共享同一个 `media_group_id`

### 新增注意：不要把图发到“别的 Telegram 对话”

实际踩坑里，Bot API 返回 `ok: true` 也不代表用户当前这个对话里真的收到了。
有一次相册成功发到了另一个 chat_id（home chat），导致当前用户会话里看不到任何图片。

因此，在 `sendDocument` / `sendPhoto` / `sendMediaGroup` 直传前，必须先确认 chat_id 是“当前对话”的那个，而不是沿用历史值。

推荐做法：
1. 先从当前会话日志确认最近一条入站消息对应的 chat_id
2. 再用这个 chat_id 调 Telegram API
3. 若用户反馈“没有发给我”，优先怀疑发错 chat_id，而不是先怀疑上传失败

可用日志搜索：
```bash
rg -n "inbound message: platform=telegram" ~/.hermes/logs/agent.log | tail -20
```

如果要锁定当前用户名/会话，再加过滤：
```bash
rg -n "inbound message: platform=telegram user=<name>" ~/.hermes/logs/agent.log | tail -20
```

### 新增注意：`sendMediaGroup` 大图相册可能比单张更慢

一次上传 4 张高分辨率 PNG 时，120 秒超时不一定代表最终方案不行；有实践里改成更长超时后成功。

经验建议：
- 大图相册直传时把超时放宽到 `300s`
- 如果第一次 `sendMediaGroup` 超时，不要立刻放弃；先重试一次，或检查是否只是客户端侧超时

### 新增注意：`sendMediaGroup` 在某些 macOS / LibreSSL 环境下也可能先报 SSL 错误

这次还遇到一个新的实际坑：
- 直接 `curl -X POST .../sendMediaGroup` 时报：
  - `curl: (35) LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to api.telegram.org:443`
- 但改成：
  - `curl --http1.1 -X POST .../sendMediaGroup`
- 同样的请求随后成功返回：
  - `"ok": true`

经验规则应补充为：
1. 如果 Telegram Bot API 的媒体组上传在本机 `curl` 上先出现 `SSL_ERROR_SYSCALL`，不要立刻判定为 token、chat_id 或文件本身有问题。
2. 优先重试同一请求，并显式加上 `--http1.1`。
3. 尤其是 multipart 上传（`sendMediaGroup` / `sendVideo` / `sendDocument`）时，`--http1.1` 往往比默认协商更稳。

推荐写法：
```bash
curl --http1.1 -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMediaGroup" \
  -F chat_id=<chat_id> \
  -F media='[...]' \
  -F img1=@/absolute/path/to/01.png \
  -F img2=@/absolute/path/to/02.png
```

### 什么时候优先用这个方案

- 用户说“给我四宫格看”
- 用户想按顺序快速预览长图内容
- 单张长图因 `PHOTO_INVALID_DIMENSIONS` 无法直接当 photo 发出
- 不想退化成 document 文件附件

## 给未来自己的操作规范

当 Telegram 用户要求“发给我”时：

1. 先判断目标类型：
   - 文本 / 图片 / 语音 / 音频 / 视频 / 文档

2. 使用匹配的原生类型思维：
   - 文本 → send_message
   - 图片 → send_photo
   - 语音气泡 → send_voice
   - 音频文件 → send_audio
   - 视频 → send_video
   - 文档 → send_document

3. 如果 `MEDIA:/path` 没成功转成原生附件：
   - 不要重复发路径
   - 立即切换到 Telegram Bot API 直传

4. 对“给我发语音”这类请求：
   - 目标最好是 `.ogg/.opus`
   - 不要默认 `.mp3` 就等于语音泡泡

5. 对“给我发文件”这类请求：
   - 默认按 document 理解
   - 特别是 PDF，优先 document 直传

## 长图与相册发送的新增经验

### 相册/九宫格发送的用户体验要求（新增）

当用户明确说：
- “一起发给我”
- “九宫格那种”
- “不要一张一张单独刷屏”

不要再用多条独立消息或多行 `MEDIA:/...` 代替相册发送。
应优先理解为：
- 使用 Telegram 原生 `sendMediaGroup`
- 以单个媒体组一次性发出
- 让 Telegram 客户端按相册/九宫格方式展示

### `sendMediaGroup` 数量上限（新增）

Telegram Bot API 的媒体组一次最多可发送 **10** 个媒体项。
因此实战规则应改为：
- **9 张**：可直接发成一组相册（常见“九宫格”体验）
- **10 张**：也可以一次性发成一个媒体组，不必拆成两组
- **超过 10 张**：再拆成多个媒体组

也就是说：
- 用户要 10 张一起发时，优先直接一个 `sendMediaGroup`
- 不要默认“9 张一组 + 1 张单发”
- 更不要退化成 10 条独立 photo 消息

### 相册发送前的图片尺寸策略（新增）

即使文件本身不大，也要先确认每张图适合作为 Telegram `photo`：
- 尺寸不要超过 Telegram photo 约束
- 尤其注意超长图时的高度/总尺寸问题

一次成功案例里：
- 10 张详情图先压成 JPEG
- 最终 Telegram 返回的 photo 展示规格约为 `921 x 2560`
- `sendMediaGroup` 返回 `ok=true`
- 10 张共享同一个 `media_group_id`

经验规则：
- 如果原图是 PNG 且较长，先压成 JPEG 再走 `sendMediaGroup` 会更稳
- 发送后若返回结果中所有消息共享同一个 `media_group_id`，才算真正按相册发成功

### 1. 长图作为 `sendPhoto` 可能被 Telegram 直接拒绝
实测中，长图 PNG `1980 x 9698` 通过 Telegram Bot API `sendPhoto` 返回：
- `Bad Request: PHOTO_INVALID_DIMENSIONS`

关键不是文件大小，而是图片尺寸规则。实战中至少要检查：
- `width + height <= 10000`
- 宽高比不能过于极端（常见资料写的是不超过 `20:1`）

例如：
- `1980 + 9698 = 11678`
- 虽然宽高比约 `4.9:1`，但总尺寸和超限，所以仍会被拒绝

### 2. 长图超限时，不要硬发整张 photo
用户如果想要“直接在聊天里看图”，不要退回只发 document。
优先策略应改为：
1. 先判断原图是否会触发 `sendPhoto` 限制
2. 如果会，按可发送的最大高度/总尺寸约束，计算**最少需要拆成几张**
3. 再把长图按阅读顺序**尽量平均切分**
4. 使用 `sendMediaGroup` 一次性发出多张 photo，方便用户四宫格/相册查看

这个策略比“盲目缩小整张图”更符合阅读体验，因为：
- 不会把字缩得太小
- 不容易再次撞上 Telegram 图片尺寸限制

### 3. 切分原则
当用户没有指定切几张时：
- 根据 Telegram photo 限制先推导最少切片数
- 再尽量平均分配每张高度
- 保证所有切片都能作为 `photo` 成功发送

当用户指定切几张（例如 4 张）时：
- 仍要先验证每张切片尺寸是否满足 Telegram photo 限制
- 然后按顺序命名并发送，例如 `01.png ... 04.png`

### 4. 一次性相册发送是更好的体验
如果目标是“让我一次看完多张图”，优先用 Telegram Bot API：
- `sendMediaGroup`

好处：
- 多张图在同一组里展示
- 用户可以直接滑动查看
- 更适合长图分段阅读

### 5. 发送前务必核对当前会话 chat_id
本次还发现一个实际坑：
- Bot API 返回 `ok: true` 不等于用户当前这个聊天一定收到了
- 可能只是发到了另一个 Telegram chat（例如 home chat / 历史 chat）

因此在手动调用 Telegram API 时，必须优先从**当前入站消息日志**确认 chat_id，再发送。
不要想当然复用别的 chat_id。

## 这次更新后的核心结论

旧认知不够完整：
- 不是 Telegram 不支持各种消息类型
- 而是 Hermes 的 `MEDIA:` 提取链路对文档类不够稳，容易让原始路径漏给用户
- 同时，超长图片即便是 PNG/JPG，也可能因为 Telegram `photo` 尺寸限制被拒绝

正确认知应该是：
- Telegram 适配器原生支持 文本/图片/语音/音频/视频/文档
- Hermes 对图片/音频/视频的 `MEDIA:` 路径处理相对更直接
- 文档类要谨慎，不要把 `MEDIA:/file.pdf` 当成绝对可靠
- 用户一旦说“你发成地址了”，就直接改走 Telegram 原生附件接口
- 用户一旦要“高清长图”，若整张图超限，优先切分成多张 photo 并用 `sendMediaGroup` 一次发出
- 手动兜底发送前，先核对当前聊天的真实 `chat_id`
