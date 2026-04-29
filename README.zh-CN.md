# hermes

这个仓库用于持续维护当前机器上 Hermes harness 会使用或曾使用过的 skills 镜像，以及相关的公共配置说明。

English version: `README.md`

## 仓库目标

- 将 `Acongm/hermes` 固定维护在 `/Users/acongm/code/github/hermes`
- 把本机 `~/.hermes/skills/` 目录镜像到 GitHub 进行版本管理
- 保证 skills 尽量通用：可复用逻辑放进 skill，本地私密配置放进 `.env`，不要提交真实凭据

## 目录结构

- `config/config.public.yaml`：脱敏后的 Hermes 配置快照
- `config/SOUL.md`：导出的 agent persona / 配置说明
- `skills/`：本机 Hermes skills 的镜像目录
- `skills/email/generic-email-daily-summary/`：通用多邮箱邮件摘要 skill
- `skills/email/generic-email-daily-summary/.env.example`：可提交的邮件配置模板
- `skills/email/generic-email-daily-summary/.env`：仅本地使用的真实配置，禁止提交

## 全仓库 skills 维护原则

- 不要在任何 `SKILL.md` 中写死个人邮箱、密码、token、chat_id、bot token、app password 等私密信息
- 示例数据应使用占位符，例如 `user@example.com`、`<your_user_id>`、`your-api-key`
- 需要本地配置时，优先在对应 skill 目录下提供 `.env.example`
- 真实 `.env` 只保留在本机，不同步到 GitHub
- 如果一个旧 skill 已被更通用的新 skill 替代，应删除旧 skill，而不是长期并存

## README 与文档说明

- `README.md`：英文版总览
- `README.zh-CN.md`：中文版总览
- `README.md` 中包含完整 skills catalog（名称、说明、仓库路径）

## 当前仓库状态说明

这次整理已覆盖整个仓库的 skills，而不只是单个 email skill，包含：
- 清理 repo 内不应保留的个人定制信息
- 修复全仓库中损坏或不通用的示例片段
- 统一强调 `.env.example` / `.env` 的配置方式
- 为整个 skills 仓库补充中英文 README
