# hermes

Personal Hermes configuration plus a maintained mirror of the local skills catalog used by Hermes harness on this machine.

## Repository purpose

- Keep `Acongm/hermes` under `/Users/acongm/code/github/hermes` for ongoing maintenance.
- Mirror the local `~/.hermes/skills/` tree into version control.
- Keep skills generic: reusable logic belongs in the skill; user-specific secrets belong in local `.env` files and must not be committed.

## Repository structure

- `config/config.public.yaml` — sanitized Hermes config snapshot
- `config/SOUL.md` — exported agent persona/config notes
- `skills/` — mirrored local Hermes skills tree
- `skills/email/generic-email-daily-summary/` — generic multi-account email summary skill
- `skills/email/generic-email-daily-summary/.env.example` — safe template for account configuration
- `skills/email/generic-email-daily-summary/.env` — local real config only; do not commit

## Skill design rules

- Do not hardcode personal email addresses, passwords, tokens, or app passwords in any `SKILL.md`.
- Put reusable behavior in the skill and provider/account-specific data in `.env.example` templates and local `.env` files.
- When a skill becomes obsolete or is superseded by a generic one, remove the legacy skill instead of keeping both.

## Secrets

- Never commit real `.env` files.
- `.env.example` files are safe templates and should use placeholders only.
- The generic email summary script loads configuration from the skill-local `.env` first, then falls back to `~/.hermes/.env`, while already-exported shell variables still win.

## Skills catalog (90 skills)

Each entry lists the skill name, a short explanation, and its path inside this repository.

### apple (4)
Apple/macOS-specific skills — iMessage, Reminders, Notes, FindMy, and macOS automation. These skills only load on macOS systems.

- `apple-notes` — Manage Apple Notes via the memo CLI on macOS (create, view, search, edit). (`skills/apple/apple-notes/SKILL.md`)
- `apple-reminders` — Manage Apple Reminders via remindctl CLI (list, add, complete, delete). (`skills/apple/apple-reminders/SKILL.md`)
- `findmy` — Track Apple devices and AirTags via FindMy.app on macOS using AppleScript and screen capture. (`skills/apple/findmy/SKILL.md`)
- `imessage` — Send and receive iMessages/SMS via the imsg CLI on macOS. (`skills/apple/imessage/SKILL.md`)

### autonomous-ai-agents (4)
Skills for spawning and orchestrating autonomous AI coding agents and multi-agent workflows — running independent agent processes, delegating tasks, and coordinating parallel workstreams.

- `claude-code` — Delegate coding tasks to Claude Code (Anthropic's CLI agent). Use for building features, refactoring, PR reviews, and iterative coding. Requires the claude CLI installed. (`skills/autonomous-ai-agents/claude-code/SKILL.md`)
- `codex` — Delegate coding tasks to OpenAI Codex CLI agent. Use for building features, refactoring, PR reviews, and batch issue fixing. Requires the codex CLI and a git repository. (`skills/autonomous-ai-agents/codex/SKILL.md`)
- `hermes-agent` — Complete guide to using and extending Hermes Agent — CLI usage, setup, configuration, spawning additional agents, gateway platforms, skills, voice, tools, profiles, and a concise contributor reference. Load this skill when helping users configure Hermes, troubleshoot issues, spawn agent instances, or make code contributions. (`skills/autonomous-ai-agents/hermes-agent/SKILL.md`)
- `opencode` — Delegate coding tasks to OpenCode CLI agent for feature implementation, refactoring, PR review, and long-running autonomous sessions. Requires the opencode CLI installed and authenticated. (`skills/autonomous-ai-agents/opencode/SKILL.md`)

### creative (9)
Creative content generation — ASCII art, hand-drawn style diagrams, and visual design tools.

- `ascii-art` — Generate ASCII art using pyfiglet (571 fonts), cowsay, boxes, toilet, image-to-ascii, remote APIs (asciified, ascii.co.uk), and LLM fallback. No API keys required. (`skills/creative/ascii-art/SKILL.md`)
- `ascii-video` — Production pipeline for ASCII art video — any format. Converts video/audio/images/generative input into colored ASCII character video output (MP4, GIF, image sequence). Covers: video-to-ASCII conversion, audio-reactive music visualizers, generative ASCII art animations, hybrid video+audio reactive, text/lyrics overlays, real-time terminal rendering. Use when users request: ASCII video, text art video, terminal-style video, character art animation, retro text visualization, audio visualizer in ASCII, converting video to ASCII art, matrix-style effects, or any animated ASCII output. (`skills/creative/ascii-video/SKILL.md`)
- `creative-ideation` — Generate project ideas through creative constraints. Use when the user says 'I want to build something', 'give me a project idea', 'I'm bored', 'what should I make', 'inspire me', or any variant of 'I have tools but no direction'. Works for code, art, hardware, writing, tools, and anything that can be made. (`skills/creative/creative-ideation/SKILL.md`)
- `excalidraw` — Create hand-drawn style diagrams using Excalidraw JSON format. Generate .excalidraw files for architecture diagrams, flowcharts, sequence diagrams, concept maps, and more. Files can be opened at excalidraw.com or uploaded for shareable links. (`skills/creative/excalidraw/SKILL.md`)
- `image-poster-fallback-macos` — Generate and finish a themed poster image on macOS when first-party image tools/API keys are unavailable, using Pollinations as a fallback, vision-based candidate selection, and Swift/AppKit text overlay for signature lines. (`skills/creative/image-poster-fallback-macos/SKILL.md`)
- `manim-video` — Production pipeline for mathematical and technical animations using Manim Community Edition. Creates 3Blue1Brown-style explainer videos, algorithm visualizations, equation derivations, architecture diagrams, and data stories. Use when users request: animated explanations, math animations, concept visualizations, algorithm walkthroughs, technical explainers, 3Blue1Brown style videos, or any programmatic animation with geometric/mathematical content. (`skills/creative/manim-video/SKILL.md`)
- `p5js` — Production pipeline for interactive and generative visual art using p5.js. Creates browser-based sketches, generative art, data visualizations, interactive experiences, 3D scenes, audio-reactive visuals, and motion graphics — exported as HTML, PNG, GIF, MP4, or SVG. Covers: 2D/3D rendering, noise and particle systems, flow fields, shaders (GLSL), pixel manipulation, kinetic typography, WebGL scenes, audio analysis, mouse/keyboard interaction, and headless high-res export. Use when users request: p5.js sketches, creative coding, generative art, interactive visualizations, canvas animations, browser-based visual art, data viz, shader effects, or any p5.js project. (`skills/creative/p5js/SKILL.md`)
- `popular-web-designs` — 54 production-quality design systems extracted from real websites. Load a template to generate HTML/CSS that matches the visual identity of sites like Stripe, Linear, Vercel, Notion, Airbnb, and more. Each template includes colors, typography, components, layout rules, and ready-to-use CSS values. (`skills/creative/popular-web-designs/SKILL.md`)
- `songwriting-and-ai-music` — Songwriting craft, AI music generation prompts (Suno focus), parody/adaptation techniques, phonetic tricks, and lessons learned. These are tools and ideas, not rules. Break any of them when the art calls for it. (`skills/creative/songwriting-and-ai-music/SKILL.md`)

### data-science (1)
Skills for data science workflows — interactive exploration, Jupyter notebooks, data analysis, and visualization.

- `jupyter-live-kernel` — Use a live Jupyter kernel for stateful, iterative Python execution via hamelnb. Load this skill when the task involves exploration, iteration, or inspecting intermediate results — data science, ML experimentation, API exploration, or building up complex code step-by-step. Uses terminal to run CLI commands against a live Jupyter kernel. No new tools required. (`skills/data-science/jupyter-live-kernel/SKILL.md`)

### devops (1)
- `webhook-subscriptions` — Create and manage webhook subscriptions for event-driven agent activation. Use when the user wants external services to trigger agent runs automatically. (`skills/devops/webhook-subscriptions/SKILL.md`)

### email (2)
Skills for sending, receiving, searching, and managing email from the terminal.

- `generic-email-daily-summary` — 通用多邮箱 24 小时邮件摘要技能。通过环境变量配置多个邮箱，由脚本抓取 JSON 后生成中文详细摘要。 (`skills/email/generic-email-daily-summary/SKILL.md`)
- `himalaya` — CLI to manage emails via IMAP/SMTP. Use himalaya to list, read, write, reply, forward, search, and organize emails from the terminal. Supports multiple accounts and message composition with MML (MIME Meta Language). (`skills/email/himalaya/SKILL.md`)

### gaming (2)
Skills for setting up, configuring, and managing game servers, modpacks, and gaming-related infrastructure.

- `minecraft-modpack-server` — Set up a modded Minecraft server from a CurseForge/Modrinth server pack zip. Covers NeoForge/Forge install, Java version, JVM tuning, firewall, LAN config, backups, and launch scripts. (`skills/gaming/minecraft-modpack-server/SKILL.md`)
- `pokemon-player` — Play Pokemon games autonomously via headless emulation. Starts a game server, reads structured game state from RAM, makes strategic decisions, and sends button inputs — all from the terminal. (`skills/gaming/pokemon-player/SKILL.md`)

### github (6)
GitHub workflow skills for managing repositories, pull requests, code reviews, issues, and CI/CD pipelines using the gh CLI and git via terminal.

- `codebase-inspection` — Inspect and analyze codebases using pygount for LOC counting, language breakdown, and code-vs-comment ratios. Use when asked to check lines of code, repo size, language composition, or codebase stats. (`skills/github/codebase-inspection/SKILL.md`)
- `github-auth` — Set up GitHub authentication for the agent using git (universally available) or the gh CLI. Covers HTTPS tokens, SSH keys, credential helpers, and gh auth — with a detection flow to pick the right method automatically. (`skills/github/github-auth/SKILL.md`)
- `github-code-review` — Review code changes by analyzing git diffs, leaving inline comments on PRs, and performing thorough pre-push review. Works with gh CLI or falls back to git + GitHub REST API via curl. (`skills/github/github-code-review/SKILL.md`)
- `github-issues` — Create, manage, triage, and close GitHub issues. Search existing issues, add labels, assign people, and link to PRs. Works with gh CLI or falls back to git + GitHub REST API via curl. (`skills/github/github-issues/SKILL.md`)
- `github-pr-workflow` — Full pull request lifecycle — create branches, commit changes, open PRs, monitor CI status, auto-fix failures, and merge. Works with gh CLI or falls back to git + GitHub REST API via curl. (`skills/github/github-pr-workflow/SKILL.md`)
- `github-repo-management` — Clone, create, fork, configure, and manage GitHub repositories. Manage remotes, secrets, releases, and workflows. Works with gh CLI or falls back to git + GitHub REST API via curl. (`skills/github/github-repo-management/SKILL.md`)

### leisure (1)
- `find-nearby` — Find nearby places (restaurants, cafes, bars, pharmacies, etc.) using OpenStreetMap. Works with coordinates, addresses, cities, zip codes, or Telegram location pins. No API keys needed. (`skills/leisure/find-nearby/SKILL.md`)

### mcp (2)
Skills for working with MCP (Model Context Protocol) servers, tools, and integrations. Includes the built-in native MCP client (configure servers in config.yaml for automatic tool discovery) and the mcporter CLI bridge for ad-hoc server interaction.

- `mcporter` — Use the mcporter CLI to list, configure, auth, and call MCP servers/tools directly (HTTP or stdio), including ad-hoc servers, config edits, and CLI/type generation. (`skills/mcp/mcporter/SKILL.md`)
- `native-mcp` — Built-in MCP (Model Context Protocol) client that connects to external MCP servers, discovers their tools, and registers them as native Hermes Agent tools. Supports stdio and HTTP transports with automatic reconnection, security filtering, and zero-config tool injection. (`skills/mcp/native-mcp/SKILL.md`)

### media (4)
Skills for working with media content — YouTube transcripts, GIF search, music generation, and audio visualization.

- `gif-search` — Search and download GIFs from Tenor using curl. No dependencies beyond curl and jq. Useful for finding reaction GIFs, creating visual content, and sending GIFs in chat. (`skills/media/gif-search/SKILL.md`)
- `heartmula` — Set up and run HeartMuLa, the open-source music generation model family (Suno-like). Generates full songs from lyrics + tags with multilingual support. (`skills/media/heartmula/SKILL.md`)
- `songsee` — Generate spectrograms and audio feature visualizations (mel, chroma, MFCC, tempogram, etc.) from audio files via CLI. Useful for audio analysis, music production debugging, and visual documentation. (`skills/media/songsee/SKILL.md`)
- `youtube-content` — Fetch YouTube video transcripts and transform them into structured content (chapters, summaries, threads, blog posts). Use when the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, or wants to extract and reformat content from any YouTube video. (`skills/media/youtube-content/SKILL.md`)

### mlops (1)
Knowledge and Tools for Machine Learning Operations - tools and frameworks for training, fine-tuning, deploying, and optimizing ML/AI models

- `huggingface-hub` — Hugging Face Hub CLI (hf) — search, download, and upload models and datasets, manage repos, query datasets with SQL, deploy inference endpoints, manage Spaces and buckets. (`skills/mlops/huggingface-hub/SKILL.md`)

### mlops/cloud (1)
GPU cloud providers and serverless compute platforms for ML workloads.

- `modal` — Serverless GPU cloud platform for running ML workloads. Use when you need on-demand GPU access without infrastructure management, deploying ML models as APIs, or running batch jobs with automatic scaling. (`skills/mlops/cloud/modal/SKILL.md`)

### mlops/evaluation (2)
Model evaluation benchmarks, experiment tracking, data curation, tokenizers, and interpretability tools.

- `lm-evaluation-harness` — Evaluates LLMs across 60+ academic benchmarks (MMLU, HumanEval, GSM8K, TruthfulQA, HellaSwag). Use when benchmarking model quality, comparing models, reporting academic results, or tracking training progress. Industry standard used by EleutherAI, HuggingFace, and major labs. Supports HuggingFace, vLLM, APIs. (`skills/mlops/evaluation/lm-evaluation-harness/SKILL.md`)
- `weights-and-biases` — Track ML experiments with automatic logging, visualize training in real-time, optimize hyperparameters with sweeps, and manage model registry with W&B - collaborative MLOps platform (`skills/mlops/evaluation/weights-and-biases/SKILL.md`)

### mlops/inference (6)
Model serving, quantization (GGUF/GPTQ), structured output, inference optimization, and model surgery tools for deploying and running LLMs.

- `gguf` — GGUF format and llama.cpp quantization for efficient CPU/GPU inference. Use when deploying models on consumer hardware, Apple Silicon, or when needing flexible quantization from 2-8 bit without GPU requirements. (`skills/mlops/inference/gguf/SKILL.md`)
- `guidance` — Control LLM output with regex and grammars, guarantee valid JSON/XML/code generation, enforce structured formats, and build multi-step workflows with Guidance - Microsoft Research's constrained generation framework (`skills/mlops/inference/guidance/SKILL.md`)
- `llama-cpp` — Runs LLM inference on CPU, Apple Silicon, and consumer GPUs without NVIDIA hardware. Use for edge deployment, M1/M2/M3 Macs, AMD/Intel GPUs, or when CUDA is unavailable. Supports GGUF quantization (1.5-8 bit) for reduced memory and 4-10× speedup vs PyTorch on CPU. (`skills/mlops/inference/llama-cpp/SKILL.md`)
- `obliteratus` — Remove refusal behaviors from open-weight LLMs using OBLITERATUS — mechanistic interpretability techniques (diff-in-means, SVD, whitened SVD, LEACE, SAE decomposition, etc.) to excise guardrails while preserving reasoning. 9 CLI methods, 28 analysis modules, 116 model presets across 5 compute tiers, tournament evaluation, and telemetry-driven recommendations. Use when a user wants to uncensor, abliterate, or remove refusal from an LLM. (`skills/mlops/inference/obliteratus/SKILL.md`)
- `outlines` — Guarantee valid JSON/XML/code structure during generation, use Pydantic models for type-safe outputs, support local models (Transformers, vLLM), and maximize inference speed with Outlines - dottxt.ai's structured generation library (`skills/mlops/inference/outlines/SKILL.md`)
- `vllm` — Serves LLMs with high throughput using vLLM's PagedAttention and continuous batching. Use when deploying production LLM APIs, optimizing inference latency/throughput, or serving models with limited GPU memory. Supports OpenAI-compatible endpoints, quantization (GPTQ/AWQ/FP8), and tensor parallelism. (`skills/mlops/inference/vllm/SKILL.md`)

### mlops/models (5)
Specific model architectures and tools — computer vision (CLIP, SAM, Stable Diffusion), speech (Whisper), audio generation (AudioCraft), and multimodal models (LLaVA).

- `audiocraft` — PyTorch library for audio generation including text-to-music (MusicGen) and text-to-sound (AudioGen). Use when you need to generate music from text descriptions, create sound effects, or perform melody-conditioned music generation. (`skills/mlops/models/audiocraft/SKILL.md`)
- `clip` — OpenAI's model connecting vision and language. Enables zero-shot image classification, image-text matching, and cross-modal retrieval. Trained on 400M image-text pairs. Use for image search, content moderation, or vision-language tasks without fine-tuning. Best for general-purpose image understanding. (`skills/mlops/models/clip/SKILL.md`)
- `segment-anything` — Foundation model for image segmentation with zero-shot transfer. Use when you need to segment any object in images using points, boxes, or masks as prompts, or automatically generate all object masks in an image. (`skills/mlops/models/segment-anything/SKILL.md`)
- `stable-diffusion` — State-of-the-art text-to-image generation with Stable Diffusion models via HuggingFace Diffusers. Use when generating images from text prompts, performing image-to-image translation, inpainting, or building custom diffusion pipelines. (`skills/mlops/models/stable-diffusion/SKILL.md`)
- `whisper` — OpenAI's general-purpose speech recognition model. Supports 99 languages, transcription, translation to English, and language identification. Six model sizes from tiny (39M params) to large (1550M params). Use for speech-to-text, podcast transcription, or multilingual audio processing. Best for robust, multilingual ASR. (`skills/mlops/models/whisper/SKILL.md`)

### mlops/research (1)
ML research frameworks for building and optimizing AI systems with declarative programming.

- `dspy` — Build complex AI systems with declarative programming, optimize prompts automatically, create modular RAG systems and agents with DSPy - Stanford NLP's framework for systematic LM programming (`skills/mlops/research/dspy/SKILL.md`)

### mlops/training (6)
Fine-tuning, RLHF/DPO/GRPO training, distributed training frameworks, and optimization tools for training LLMs and other models.

- `axolotl` — Expert guidance for fine-tuning LLMs with Axolotl - YAML configs, 100+ models, LoRA/QLoRA, DPO/KTO/ORPO/GRPO, multimodal support (`skills/mlops/training/axolotl/SKILL.md`)
- `grpo-rl-training` — Expert guidance for GRPO/RL fine-tuning with TRL for reasoning and task-specific model training (`skills/mlops/training/grpo-rl-training/SKILL.md`)
- `peft` — Parameter-efficient fine-tuning for LLMs using LoRA, QLoRA, and 25+ methods. Use when fine-tuning large models (7B-70B) with limited GPU memory, when you need to train <1% of parameters with minimal accuracy loss, or for multi-adapter serving. HuggingFace's official library integrated with transformers ecosystem. (`skills/mlops/training/peft/SKILL.md`)
- `pytorch-fsdp` — Expert guidance for Fully Sharded Data Parallel training with PyTorch FSDP - parameter sharding, mixed precision, CPU offloading, FSDP2 (`skills/mlops/training/pytorch-fsdp/SKILL.md`)
- `trl-fine-tuning` — Fine-tune LLMs using reinforcement learning with TRL - SFT for instruction tuning, DPO for preference alignment, PPO/GRPO for reward optimization, and reward model training. Use when need RLHF, align model with preferences, or train from human feedback. Works with HuggingFace Transformers. (`skills/mlops/training/trl-fine-tuning/SKILL.md`)
- `unsloth` — Expert guidance for fast fine-tuning with Unsloth - 2-5x faster training, 50-80% less memory, LoRA/QLoRA optimization (`skills/mlops/training/unsloth/SKILL.md`)

### note-taking (1)
Note taking skills, to save information, assist with research, and collab on multi-session planning and information sharing.

- `obsidian` — Read, search, and create notes in the Obsidian vault. (`skills/note-taking/obsidian/SKILL.md`)

### openclaw-imports (1)
- `find-skills` — Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. (`skills/openclaw-imports/find-skills/SKILL.md`)

### productivity (8)
Skills for document creation, presentations, spreadsheets, and other productivity workflows.

- `google-workspace` — Gmail, Calendar, Drive, Contacts, Sheets, and Docs integration via gws CLI (googleworkspace/cli). Uses OAuth2 with automatic token refresh via bridge script. Requires gws binary. (`skills/productivity/google-workspace/SKILL.md`)
- `linear` — Manage Linear issues, projects, and teams via the GraphQL API. Create, update, search, and organize issues. Uses API key auth (no OAuth needed). All operations via curl — no dependencies. (`skills/productivity/linear/SKILL.md`)
- `nano-pdf` — Edit PDFs with natural-language instructions using the nano-pdf CLI. Modify text, fix typos, update titles, and make content changes to specific pages without manual editing. (`skills/productivity/nano-pdf/SKILL.md`)
- `notion` — Notion API for creating and managing pages, databases, and blocks via curl. Search, create, update, and query Notion workspaces directly from the terminal. (`skills/productivity/notion/SKILL.md`)
- `ocr-and-documents` — Extract text from PDFs and scanned documents. Use web_extract for remote URLs, pymupdf for local text-based PDFs, marker-pdf for OCR/scanned docs. For DOCX use python-docx, for PPTX see the powerpoint skill. (`skills/productivity/ocr-and-documents/SKILL.md`)
- `powerpoint` — Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill. (`skills/productivity/powerpoint/SKILL.md`)
- `smtp-debug-vpn` — Diagnose and resolve SMTP email sending failures caused by VPN/proxy interference (`skills/productivity/smtp-debug-vpn/SKILL.md`)
- `text-to-pdf-macos` — Convert UTF-8 plain text into a readable multipage PDF on macOS using built-in Swift/AppKit/CoreText when pandoc or LibreOffice are unavailable. (`skills/productivity/text-to-pdf-macos/SKILL.md`)

### red-teaming (1)
- `godmode` — Jailbreak API-served LLMs using G0DM0D3 techniques — Parseltongue input obfuscation (33 techniques), GODMODE CLASSIC system prompt templates, ULTRAPLINIAN multi-model racing, encoding escalation, and Hermes-native prefill/system prompt integration. Use when a user wants to bypass safety filters, jailbreak a model, or red-team model robustness. (`skills/red-teaming/godmode/SKILL.md`)

### research (6)
Skills for academic research, paper discovery, literature review, domain reconnaissance, market data, content monitoring, and scientific knowledge retrieval.

- `arxiv` — Search and retrieve academic papers from arXiv using their free REST API. No API key needed. Search by keyword, author, category, or ID. Combine with web_extract or the ocr-and-documents skill to read full paper content. (`skills/research/arxiv/SKILL.md`)
- `blogwatcher` — Monitor blogs and RSS/Atom feeds for updates using the blogwatcher-cli tool. Add blogs, scan for new articles, track read status, and filter by category. (`skills/research/blogwatcher/SKILL.md`)
- `daily-tech-news-pdf` — 生成每日科技新闻 PDF 摘要，重点覆盖前端、DevOps、AI 三个方向并保持同等权重；适用于定时任务自动投递。 (`skills/research/daily-tech-news-pdf/SKILL.md`)
- `llm-wiki` — Karpathy's LLM Wiki — build and maintain a persistent, interlinked markdown knowledge base. Ingest sources, query compiled knowledge, and lint for consistency. (`skills/research/llm-wiki/SKILL.md`)
- `polymarket` — Query Polymarket prediction market data — search markets, get prices, orderbooks, and price history. Read-only via public REST APIs, no API key needed. (`skills/research/polymarket/SKILL.md`)
- `research-paper-writing` — End-to-end pipeline for writing ML/AI research papers — from experiment design through analysis, drafting, revision, and submission. Covers NeurIPS, ICML, ICLR, ACL, AAAI, COLM. Integrates automated experiment monitoring, statistical analysis, iterative writing, and citation verification. (`skills/research/research-paper-writing/SKILL.md`)

### root (1)
- `dogfood` — Systematic exploratory QA testing of web applications — find bugs, capture evidence, and generate structured reports (`skills/dogfood/SKILL.md`)

### smart-home (1)
Skills for controlling smart home devices — lights, switches, sensors, and home automation systems.

- `openhue` — Control Philips Hue lights, rooms, and scenes via the OpenHue CLI. Turn lights on/off, adjust brightness, color, color temperature, and activate scenes. (`skills/smart-home/openhue/SKILL.md`)

### social-media (6)
Skills for interacting with social platforms and social-media workflows — posting, reading, monitoring, and account operations.

- `hermes-weixin-send-debug` — Diagnose Hermes Weixin send failures, especially duplicate token-lock conflicts and recipient identification issues (`skills/social-media/hermes-weixin-send-debug/SKILL.md`)
- `openclaw-troubleshooting` — OpenClaw 故障排查指南 — Gateway 启动、Telegram 频道配置、配对问题 (`skills/social-media/openclaw-troubleshooting/SKILL.md`)
- `telegram-native-file-delivery` — Telegram 原生消息/附件发送指南：区分文本、图片、语音、音频、视频、文档的正确投递方式，并在 MEDIA:/path 失败或降级为路径文本时使用 Telegram 原生接口兜底。 (`skills/social-media/telegram-native-file-delivery/SKILL.md`)
- `telegram-polling-conflict-debug` — 诊断 Telegram Bot 收不到消息的问题，特别是"polling conflict"错误 (`skills/social-media/telegram-polling-conflict-debug/SKILL.md`)
- `x-browser-screenshot-capture` — Capture readable screenshots of X/Twitter posts or articles in the browser tool, including workarounds for blank-white screenshots and blurry full-page captures. (`skills/social-media/x-browser-screenshot-capture/SKILL.md`)
- `xitter` — Interact with X/Twitter via the x-cli terminal client using official X API credentials. Use for posting, reading timelines, searching tweets, liking, retweeting, bookmarks, mentions, and user lookups. (`skills/social-media/xitter/SKILL.md`)

### software-development (7)
- `opencli-install-browser-bridge` — Install OpenCLI on macOS/Linux, verify the daemon, and connect the Chrome Browser Bridge extension so local logged-in browser sessions can be reused. (`skills/software-development/opencli-install-browser-bridge/SKILL.md`)
- `plan` — Plan mode for Hermes — inspect context, write a markdown plan into the active workspace's `.hermes/plans/` directory, and do not execute the work. (`skills/software-development/plan/SKILL.md`)
- `requesting-code-review` — Pre-commit verification pipeline — static security scan, baseline-aware quality gates, independent reviewer subagent, and auto-fix loop. Use after code changes and before committing, pushing, or opening a PR. (`skills/software-development/requesting-code-review/SKILL.md`)
- `subagent-driven-development` — Use when executing implementation plans with independent tasks. Dispatches fresh delegate_task per task with two-stage review (spec compliance then code quality). (`skills/software-development/subagent-driven-development/SKILL.md`)
- `systematic-debugging` — Use when encountering any bug, test failure, or unexpected behavior. 4-phase root cause investigation — NO fixes without understanding the problem first. (`skills/software-development/systematic-debugging/SKILL.md`)
- `test-driven-development` — Use when implementing any feature or bugfix, before writing implementation code. Enforces RED-GREEN-REFACTOR cycle with test-first approach. (`skills/software-development/test-driven-development/SKILL.md`)
- `writing-plans` — Use when you have a spec or requirements for a multi-step task. Creates comprehensive implementation plans with bite-sized tasks, exact file paths, and complete code examples. (`skills/software-development/writing-plans/SKILL.md`)
