---
name: daily-tech-news-pdf
description: 生成每日科技新闻 PDF 摘要，重点覆盖前端、DevOps、AI 三个方向并保持同等权重；适用于定时任务自动投递。
triggers:
  - 用户要求把每日新闻整理成 PDF
  - 用户要求定时抓取前端、DevOps、AI 新闻
  - 需要把网页检索结果整理为可投递 PDF 文件
---

# 每日科技新闻 PDF

## 目标
生成一份适合聊天窗口投递的 PDF 文件，内容来自以下三个领域，且权重相同：
- 前端
- DevOps
- AI

“权重相同”含义：
- 选题时三类都必须出现
- 不允许只偏向某一类
- 默认每类 2~3 条，总计 6~9 条
- 如果某一类当天有效新闻较少，可降到 1 条，但另外两类也不要明显堆叠，整体仍保持尽量均衡

## 检索范围
优先级：
1. 最近 24 小时
2. 如果太少，可扩展到最近 72 小时
3. 再不足时，可补最近 7 天内最值得关注的更新

## 建议检索主题
### 前端
- JavaScript
- TypeScript
- React
- Vue
- Next.js
- Node.js
- Vite
- Chrome / WebKit / Firefox
- CSS
- Web AI
- 前端工程化 / 开发工具

### DevOps
- Docker
- Kubernetes
- GitHub Actions
- CI/CD
- Terraform
- OpenTofu
- Cloud Native
- Observability
- Prometheus / Grafana
- 容器安全
- 平台工程 / Infra / SRE

### AI
- 大模型 / LLM
- OpenAI / Anthropic / Google / Meta / Mistral / xAI / DeepSeek 等模型或平台更新
- AI coding agents
- 开源模型发布
- 推理 / 训练 / RAG / agents / 多模态
- AI 基础设施与工具链

## 信息筛选标准
优先保留：
- 官方发布
- 版本更新
- 新能力发布
- 重要生态变化
- 影响开发者工作流的新闻
- 有明确来源和链接

尽量避免：
- 重复转述
- 无明确来源的营销软文
- 只有标题党、无实质信息的文章

## 输出内容结构
先整理成 UTF-8 纯文本，再转换为 PDF。

建议文本结构：

1. 标题
   - 今日科技新闻摘要
   - 副标题可写日期与时间范围

2. 概览
   - 日期
   - 统计：前端 N 条 / DevOps N 条 / AI N 条 / 合计 N 条
   - 一句话说明今天的整体趋势

3. 分栏目正文
   - 一、前端
   - 二、DevOps
   - 三、AI

4. 每条新闻统一格式
   - 标题
   - 来源
   - 链接
   - 一句话摘要
   - 为什么值得关注

5. 结尾
   - 今日重点观察（3~5 句）
   - 总结这三类技术的共同趋势与变化

## 写作要求
- 全文简体中文
- 简洁、清晰、信息密度高
- 不写空话
- “为什么值得关注”必须面向技术从业者
- 不要编造未在来源中出现的事实
- 同一类别内按重要性排序
- 三个类别的篇幅要尽量均衡

## PDF 生成要求
使用 `text-to-pdf-macos` 技能的做法：
1. 先将最终文本写入 UTF-8 `.txt`
2. 优先使用 `cupsfilter` 转成 PDF
3. 确认 PDF 存在且非空
4. 最终把 PDF 文件作为附件发送，而不是只返回路径文本

## 推荐文件命名
- 文本：`/tmp/daily-tech-news-YYYY-MM-DD.txt`
- PDF：`/tmp/daily-tech-news-YYYY-MM-DD.pdf`

## 定时任务场景的最终响应
定时任务最终响应建议包含：
1. 一句简短说明，例如：`已生成今天的科技新闻 PDF，包含前端、DevOps、AI 三类均衡摘要。`
2. 紧接真实附件：`MEDIA:/absolute/path/to/pdf`

## 质量检查
完成前确认：
- 三个分类都存在
- 各分类条数大致均衡
- 每条都有来源和链接
- PDF 文件存在且大小大于 0
- 最终发送的是 PDF 附件本身
