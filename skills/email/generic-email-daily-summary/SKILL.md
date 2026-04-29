---
name: generic-email-daily-summary
description: 通用多邮箱 24 小时邮件摘要技能。通过环境变量配置多个邮箱，由脚本抓取 JSON 后生成中文详细摘要。
---

# 通用多邮箱 24 小时邮件摘要

## 适用场景
- 一个或多个邮箱需要做过去 24 小时邮件摘要
- 定时任务或手动执行会先运行 skill 内置脚本 `scripts/email_summary_last24h.py`
- 脚本输出标准 JSON，再由 skill 生成适合 Telegram/聊天窗口阅读的中文详细摘要

## 配置方式
邮箱列表不写死在 skill 里，而是通过环境变量提供。

关键环境变量：
- `HERMES_EMAIL_ACCOUNTS_JSON`
- 各邮箱密码分别放到独立环境变量中，例如：
  - `HERMES_EMAIL_126_APP_PASSWORD`
  - `HERMES_EMAIL_GMAIL_APP_PASSWORD`

### HERMES_EMAIL_ACCOUNTS_JSON 示例
```json
[
  {
    "label": "126",
    "email": "acongm@126.com",
    "host": "imap.126.com",
    "port": 993,
    "folder": "INBOX",
    "password_env": "HERMES_EMAIL_126_APP_PASSWORD",
    "imap_id_workaround": true
  },
  {
    "label": "gmail",
    "email": "o.arvin.peng@gmail.com",
    "host": "imap.gmail.com",
    "port": 993,
    "folder": "INBOX",
    "password_env": "HERMES_EMAIL_GMAIL_APP_PASSWORD"
  }
]
```

## 技能目录结构
- `SKILL.md`：摘要规则与输出格式
- `scripts/email_summary_last24h.py`：多邮箱 IMAP 抓取脚本

## 脚本输出假设
脚本会输出：
- `window_start`
- `window_end`
- `generated_at`
- `account_count`
- `accounts[]`
- `count`
- `emails[]`

每封邮件通常包含：
- `account`
- `email`
- `date_local`
- `from`
- `subject`
- `preview`
- `body_length`

## 输出格式
按下面结构输出：

1. 标题：`过去24小时邮件摘要`
2. 时间范围：显示 `window_start` 到 `window_end`
3. 总数：`邮件总数：N 封`
4. 按重要性分组：
   - `一、建议关注`
   - `二、通知 / 促销类`
   - `三、其他`
5. 每封邮件使用详细版格式：
   - 邮箱账户（如果是多邮箱，必须标出）
   - 时间
   - 发件人
   - 主题
   - 详细摘要（2~5 句，基于 preview 提炼）
   - 结论标签：`建议关注` / `可忽略`
6. 结尾加：
   - `如果需要，我可以继续帮你读某一封的完整内容。`

## 分类规则
### 建议关注
满足任一项可归入“建议关注”：
- 安全提醒 / 新设备登录 / 验证码 / 账号风险
- 银行 / 信用卡 / 支付 / 账单 / 扣费 / 发票
- GitHub / 云服务 / 开发平台的计费规则变化
- 人工来信 / 工作事务 / 系统告警

### 通知 / 促销类
满足任一项可归入“通知 / 促销类”：
- 营销、折扣、升级优惠、广告
- 社交平台推荐好友、订阅提醒
- 与金钱、账号安全、工作任务无直接关系的常规通知

### 其他
无法明确判断且信息量较低时归为“其他”。

## 摘要写法要求
- 不要原样复述 HTML/CSS、模板噪音、追踪链接
- 要把 preview 中的关键事实提炼成人类可读语言
- 对营销类邮件，明确指出它是促销/通知，并标注可忽略
- 对安全/账单/计费变更类邮件，明确说明为什么值得关注
- 不要编造 preview 里没有出现的事实
- 如果某个账户抓取失败，单独说明该账户失败，不影响其他账户摘要

## 无邮件时
如果总 count 为 0，直接输出：
`过去24小时没有新邮件。`

## 风格
- 中文
- 清晰
- 详细版
- 适合 Telegram 直接阅读
