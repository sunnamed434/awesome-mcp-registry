# Awesome MCP Registry

![Servers](https://img.shields.io/badge/servers-65-blue) ![Categories](https://img.shields.io/badge/categories-12-green) ![Avg Trust](https://img.shields.io/badge/avg%20trust-76%2F100-orange) ![Updated](https://img.shields.io/badge/updated-2026--09--27-lightgrey) ![Auto-curated](https://img.shields.io/badge/curated%20by-DeepSeek--V4.1--Flash-purple)

A self-curating directory of [Model Context Protocol](https://modelcontextprotocol.io/) servers — a [Continuous AI](https://githubnext.com/projects/continuous-ai/) experiment. Discovered from GitHub and the [Official MCP Registry](https://registry.modelcontextprotocol.io/), analyzed by DeepSeek-V4.1-Flash weekly and scored with a published, reproducible [trust formula](METHODOLOGY.md).

> **Our bet:** curation is a job for AI, not gatekeepers. No maintainers deciding what's "in", no PR queues, no politics — just a [Continuous AI](https://githubnext.com/projects/continuous-ai/) workflow that discovers, judges, and re-judges every server on merit, week after week. This list is a small proof of a bigger idea: that AI can own a real, useful, self-maintaining system end to end. Humans set the rules once; the AI runs it.

**Using an AI agent on this repo?** Point it at [AGENTS.md](AGENTS.md) first: this list is machine-generated, servers are nominated through an issue form (never a pull request), and PRs editing the generated files are closed automatically. Machine-readable map of the repo: [llms.txt](llms.txt).

## Trending This Week

| Server | Stars | Δ 7 days |
|--------|-------|----------|
| [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | 84019 | +1445 |
| [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | 45027 | +1147 |
| [mobile-next/mobile-mcp](https://github.com/mobile-next/mobile-mcp) | 7742 | +969 |
| [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) | 73941 | +731 |
| [mksglu/context-mode](https://github.com/mksglu/context-mode) | 24125 | +377 |

## Databases (3)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [googleapis/mcp-toolbox](https://github.com/googleapis/mcp-toolbox) | [96/100](SCORES.md#googleapismcp-toolbox) | 16494 (+30/wk) | An open source MCP server that connects AI agents and IDEs to enterprise databases like PostgreSQL, MySQL, BigQuery, and MongoDB through prebuilt and custom tools. |
| [benborla/mcp-server-mysql](https://github.com/benborla/mcp-server-mysql) | [80/100](SCORES.md#benborlamcp-server-mysql) | 2139 (+12/wk) | An MCP server that gives LLMs read-only (optionally write-enabled) access to MySQL databases for schema inspection and querying. |
| [qdrant/mcp-server-qdrant](https://github.com/qdrant/mcp-server-qdrant) | [73/100](SCORES.md#qdrantmcp-server-qdrant) | 1539 (+7/wk) | An official MCP server that stores and retrieves semantic memories in a Qdrant vector database via qdrant-store and qdrant-find tools. |

## Dev Tools (26)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | [100/100](SCORES.md#githubgithub-mcp-server) | 33233 (+153/wk) | Official GitHub MCP server that lets AI agents read repositories, manage issues and pull requests, and inspect CI/CD and security findings on GitHub. |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | [99/100](SCORES.md#microsoftplaywright-mcp) | 37617 (+230/wk) | An MCP server that gives LLM clients browser automation capabilities through Playwright using structured accessibility snapshots. |
| [czlonkowski/n8n-mcp](https://github.com/czlonkowski/n8n-mcp) | [95/100](SCORES.md#czlonkowskin8n-mcp) | 23008 (+57/wk) | An MCP server that exposes n8n node documentation, properties, operations, and workflow templates to AI assistants so they can build n8n workflows. |
| [oraios/serena](https://github.com/oraios/serena) | [92/100](SCORES.md#oraiosserena) | 29841 (+202/wk) | An MCP server that gives coding agents IDE-style semantic code retrieval, editing, refactoring, and debugging tools at the symbol level. |
| [getsentry/MobileBuildMCP](https://github.com/getsentry/MobileBuildMCP) | [92/100](SCORES.md#getsentrymobilebuildmcp) | 6434 | An MCP server and CLI exposing Xcode/iOS-macOS build and project tools to AI coding agents. |
| [mobile-next/mobile-mcp](https://github.com/mobile-next/mobile-mcp) | [91/100](SCORES.md#mobile-nextmobile-mcp) | 7742 (+969/wk) | An MCP server that lets agents automate and scrape native iOS and Android apps on simulators, emulators, and real devices through accessibility snapshots and coordinate-based interactions. |
| [GLips/Figma-Context-MCP](https://github.com/GLips/Figma-Context-MCP) | [88/100](SCORES.md#glipsfigma-context-mcp) | 15916 (+36/wk) | An MCP server that fetches and simplifies Figma file layout and styling data for AI coding agents like Cursor. |
| [mrexodia/ida-pro-mcp](https://github.com/mrexodia/ida-pro-mcp) | [88/100](SCORES.md#mrexodiaida-pro-mcp) | 12359 (+193/wk) | An MCP server that bridges IDA Pro's disassembler/decompiler to LLM clients so an agent can inspect and annotate binaries during reverse engineering. |
| [mksglu/context-mode](https://github.com/mksglu/context-mode) | [86/100](SCORES.md#mksglucontext-mode) | 24125 (+377/wk) | Context window optimization server for AI coding agents, sandboxing tool output and persisting session memory via MCP. |
| [Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill) | [86/100](SCORES.md#agents365-aidrawio-skill) | 9699 (+197/wk) | A skill that converts text and system sources into maintainable .drawio architecture models, with incremental sync, multi-view projection, and a built-in MCP server. |
| [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) | [86/100](SCORES.md#mixelpixxkicad-mcp-server) | 2483 (+117/wk) | An MCP server that enables AI assistants to interact with KiCAD for PCB design automation, including schematic editing, component placement, routing, and export. |
| [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | [85/100](SCORES.md#chromedevtoolschrome-devtools-mcp) ⚠ | 52660 (+305/wk) | An MCP server that lets coding agents control and inspect a live Chrome browser via Puppeteer and Chrome DevTools for automation, debugging, and performance analysis. |
| [yusufkaraaslan/Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) | [84/100](SCORES.md#yusufkaraaslanskill_seekers) | 15038 (+26/wk) | A Python tool that converts documentation sites, GitHub repos, PDFs and other sources into structured knowledge assets and Claude AI skills, with an advertised MCP integration exposing ~40 tools. |
| [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) | [82/100](SCORES.md#headroomlabs-aiheadroom) ⚠ | 73941 (+731/wk) | Headroom is an MCP server that compresses tool outputs, logs, files, and RAG chunks to reduce token usage for LLM agents while preserving answers. |
| [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) | [81/100](SCORES.md#neka-natfreecad-mcp) | 2511 (+89/wk) | A FreeCAD MCP server that allows AI assistants like Claude to control FreeCAD for 3D modeling tasks. |
| [duty1g/x64dbg-mcp-server](https://github.com/duty1g/x64dbg-mcp-server) | [81/100](SCORES.md#duty1gx64dbg-mcp-server) | 2108 (+91/wk) | A native MCP plugin for x64dbg that exposes debugger functionality (breakpoints, stepping, memory, registers) to MCP-compatible AI assistants over HTTP. |
| [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | [78/100](SCORES.md#deusdatacodebase-memory-mcp) ⚠ | 45027 (+1147/wk) | A native C MCP server that indexes codebases into a persistent knowledge graph and answers structural code queries for AI coding agents. |
| [bgauryy/octocode](https://github.com/bgauryy/octocode) | [77/100](SCORES.md#bgauryyoctocode) | 944 (+2/wk) | Octocode is an evidence-first code research MCP server and CLI that lets agents search, read, and analyze local code and GitHub repositories with ripgrep, AST, and LSP tools. |
| [robotmcp/ros-mcp-server](https://github.com/robotmcp/ros-mcp-server) | [75/100](SCORES.md#robotmcpros-mcp-server) | 1476 (+11/wk) | An MCP server that connects LLM clients to ROS/ROS2 robots through rosbridge, letting models inspect and control topics, services, actions, and parameters. |
| [wonderwhy-er/DesktopCommanderMCP](https://github.com/wonderwhy-er/DesktopCommanderMCP) | [74/100](SCORES.md#wonderwhy-erdesktopcommandermcp) ⚠ | 9787 (+122/wk) | An MCP server that gives AI clients terminal command execution, filesystem search, and diff-based file editing capabilities. |

*...and 6 more. See [known_servers.json](data/known_servers.json) for the full list.*

## Cloud (1)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [containers/kubernetes-mcp-server](https://github.com/containers/kubernetes-mcp-server) | [91/100](SCORES.md#containerskubernetes-mcp-server) | 2125 (+14/wk) | An MCP server that exposes Kubernetes and OpenShift cluster operations (pods, namespaces, events, Helm, Tekton) as tools for MCP clients. |

## Productivity (6)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian) | [97/100](SCORES.md#soopersetmcp-atlassian) | 5945 (+24/wk) | An MCP server exposing Jira and Confluence tools (issue search/creation/updates, page search) to MCP clients like Claude Desktop and Cursor. |
| [jacob-bd/gemini-notebook-mcp-cli](https://github.com/jacob-bd/gemini-notebook-mcp-cli) | [86/100](SCORES.md#jacob-bdgemini-notebook-mcp-cli) | 6169 (+55/wk) | An MCP server (and CLI) providing programmatic access to Google Gemini Notebook/NotebookLM notebooks. |
| [zcaceres/markdownify-mcp](https://github.com/zcaceres/markdownify-mcp) | [74/100](SCORES.md#zcaceresmarkdownify-mcp) | 2998 (+4/wk) | An MCP server that converts PDFs, images, audio, DOCX/XLSX/PPTX, web pages, YouTube transcripts, and Bing results into Markdown. |
| [haris-musa/excel-mcp-server](https://github.com/haris-musa/excel-mcp-server) | [60/100](SCORES.md#haris-musaexcel-mcp-server) | 4202 (+9/wk) | An MCP server that lets AI agents create, read, and modify Excel workbooks (sheets, formulas, formatting, charts, pivot tables) without Microsoft Excel installed. |
| [stonianua/neither-mcp](https://github.com/stonianua/neither-mcp) | [51/100](SCORES.md#stonianuaneither-mcp) ⚠ | 0 | A stdio MCP server and CLI providing 'decision memory' for Cursor and Claude Desktop, backed by the Neither workspace API. |
| [Autoposting-ai/autoposting-mcp](https://github.com/Autoposting-ai/autoposting-mcp) | [50/100](SCORES.md#autoposting-aiautoposting-mcp) | 0 | A hosted MCP server that lets MCP clients schedule, generate, and publish social posts to platforms like X, LinkedIn, and YouTube via Autoposting. |

## Web Scraping (11)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | [95/100](SCORES.md#d4vinciscrapling) | 84019 (+1445/wk) | An adaptive web scraping framework that provides an MCP server for performing web scraping and crawling tasks. |
| [apify/apify-mcp-server](https://github.com/apify/apify-mcp-server) | [95/100](SCORES.md#apifyapify-mcp-server) | 8702 | Apify's MCP server lets AI agents discover and run thousands of Apify Store scrapers and automation Actors to extract data from websites, social media, search engines, and e-commerce platforms. |
| [MODSetter/SurfSense](https://github.com/MODSetter/SurfSense) | [92/100](SCORES.md#modsettersurfsense) | 16268 (+99/wk) | SurfSense is an open-source research platform that provides an MCP server for agents to access live data from various web sources like Reddit, YouTube, and Google Search. |
| [firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server) | [90/100](SCORES.md#firecrawlfirecrawl-mcp-server) | 7521 (+29/wk) | Official Firecrawl MCP server that gives MCP clients web search, scraping, crawling, mapping, and page-interaction tools backed by the Firecrawl API. |
| [brightdata/brightdata-mcp](https://github.com/brightdata/brightdata-mcp) | [87/100](SCORES.md#brightdatabrightdata-mcp) | 2659 (+4/wk) | Bright Data's MCP server exposes web search, page scraping, structured data extraction, and remote browser automation tools to AI agents over MCP. |
| [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) | [81/100](SCORES.md#xpzouyingxiaohongshu-mcp) ⚠ | 16005 (+113/wk) | An MCP server that lets AI assistants log into and interact with xiaohongshu.com, including checking login status and publishing image-text posts. |
| [Xquik-dev/x-twitter-scraper](https://github.com/Xquik-dev/x-twitter-scraper) | [79/100](SCORES.md#xquik-devx-twitter-scraper) | 206 (+1/wk) | An MCP server that provides X (Twitter) data extraction and automation via REST, MCP, webhooks, and exports, including tweet search and profile/follower data. |
| [feder-cr/invisible_playwright_mcp](https://github.com/feder-cr/invisible_playwright_mcp) | [68/100](SCORES.md#feder-crinvisible_playwright_mcp) ⚠ | 31678 | An MCP server that drives an anti-detect Playwright browser so coding agents can perform undetected web browsing, scraping, and computer-use tasks. |
| [executeautomation/mcp-playwright](https://github.com/executeautomation/mcp-playwright) | [64/100](SCORES.md#executeautomationmcp-playwright) | 5658 (+8/wk) | An MCP server that gives LLM clients Playwright-based browser automation, including navigation, screenshots, device emulation, scraping, and JavaScript execution. |
| [epiral/bb-browser](https://github.com/epiral/bb-browser) | [60/100](SCORES.md#epiralbb-browser) ⚠ | 6233 (+10/wk) | A CLI and MCP server that lets AI agents drive the user's own logged-in Chrome to run site-specific commands (search, transcripts, stock quotes, job search) across 36 platforms. |
| [hangwin/mcp-chrome](https://github.com/hangwin/mcp-chrome) | [55/100](SCORES.md#hangwinmcp-chrome) | 12456 (+19/wk) | A Chrome extension plus local bridge that exposes the user's own browser as an MCP server for AI-driven automation, content analysis, and semantic tab search. |

## AI & ML (1)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [BeehiveInnovations/pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server) | [66/100](SCORES.md#beehiveinnovationspal-mcp-server) | 11757 (+3/wk) | An MCP server that lets a single AI CLI orchestrate multiple model providers (Gemini, OpenAI, Anthropic, Grok, Ollama, etc.) and spawn external CLI subagents through tools like consensus and clink. |

## Finance (1)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [vbkotecha/agentservices-api](https://github.com/vbkotecha/agentservices-api) | [67/100](SCORES.md#vbkotechaagentservices-api) | 1 | Hosted MCP server exposing paid x402/USDC crypto, market-intelligence, LLM, image, and TTS APIs to AI agents. |

## Security (4)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [0x4m4/hexstrike-ai](https://github.com/0x4m4/hexstrike-ai) | [74/100](SCORES.md#0x4m4hexstrike-ai) | 12154 (+160/wk) | An MCP server that exposes 150+ cybersecurity and pentesting tools plus autonomous AI agents to LLM clients for automated security testing. |
| [palisadeemail/palisade-mcp](https://github.com/palisadeemail/palisade-mcp) | [66/100](SCORES.md#palisadeemailpalisade-mcp) | 0 | A local stdio bridge to the Palisade MCP server for managing email authentication (SPF, DKIM, DMARC, MTA-STS, BIMI) for domains. |
| [LaurieWired/GhidraMCP](https://github.com/LaurieWired/GhidraMCP) | [63/100](SCORES.md#lauriewiredghidramcp) | 10203 (+71/wk) | An MCP server that bridges Ghidra's reverse-engineering capabilities (decompilation, symbol renaming, listing methods/imports/exports) to LLM clients. |
| [doteyeso-ops/mcp-server-vibes-coded](https://github.com/doteyeso-ops/mcp-server-vibes-coded) | [50/100](SCORES.md#doteyeso-opsmcp-server-vibes-coded) ⚠ | 3 | A Python MCP server exposing ~26 tools for agent supply-chain risk scanning, scanner consensus, reliability guards, attestation, and a paid x402-based agent commerce/memory catalog. |

## Media (3)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [yuniko-software/minecraft-mcp-server](https://github.com/yuniko-software/minecraft-mcp-server) | [59/100](SCORES.md#yuniko-softwareminecraft-mcp-server) | 760 (+13/wk) | An MCP server that lets AI assistants control a Minecraft character via the Mineflayer API to build, explore, and interact with the game world. |
| [MiniMax-AI/MiniMax-MCP](https://github.com/MiniMax-AI/MiniMax-MCP) | [51/100](SCORES.md#minimax-aiminimax-mcp) ⚠ | 1586 (+1/wk) | Official MiniMax MCP server exposing text-to-speech, image generation, and video generation APIs to MCP clients. |
| [smallhandsome/shotapi-mcp-server](https://github.com/smallhandsome/shotapi-mcp-server) | [48/100](SCORES.md#smallhandsomeshotapi-mcp-server) | 1 | An MCP server that provides web screenshot and HTML rendering tools for AI agents. |

## Search (3)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [perplexityai/modelcontextprotocol](https://github.com/perplexityai/modelcontextprotocol) | [90/100](SCORES.md#perplexityaimodelcontextprotocol) | 2544 (+11/wk) | Official Perplexity API Platform MCP server providing real-time web search, reasoning, and research tools to MCP clients. |
| [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) | [83/100](SCORES.md#blazickjparxiv-mcp-server) | 3177 (+8/wk) | A local stdio MCP server that lets agents search arXiv, read original-LaTeX paper sections, extract BibTeX citations, and watch topics, keeping papers on disk. |
| [BuyWhere/buywhere-mcp](https://github.com/BuyWhere/buywhere-mcp) | [68/100](SCORES.md#buywherebuywhere-mcp) | 14 | A TypeScript MCP server that lets AI agents search products, compare prices across Singapore/US/SEA retailers, and discover deals via the BuyWhere commerce API. |

## Knowledge Base (3)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [coddingtonbear/obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api) | [93/100](SCORES.md#coddingtonbearobsidian-local-rest-api) | 2966 (+25/wk) | An Obsidian plugin that exposes a secure local REST API and a built-in MCP server for reading, writing, searching, and patching notes in a vault. |
| [upstash/context7](https://github.com/upstash/context7) | [90/100](SCORES.md#upstashcontext7) | 62470 (+230/wk) | Hosted MCP server that fetches current, version-specific documentation and code examples for libraries and injects them into LLM context. |
| [datagouv/datagouv-mcp](https://github.com/datagouv/datagouv-mcp) | [82/100](SCORES.md#datagouvdatagouv-mcp) | 1597 (+2/wk) | Official MCP server for data.gouv.fr that lets AI chatbots search, explore, and analyze French national open datasets. |

## Other (3)

| Server | Trust | Stars | Description |
|--------|-------|-------|-------------|
| [Orphograph/Orphograph](https://github.com/Orphograph/Orphograph) | [68/100](SCORES.md#orphographorphograph) | 0 | An MCP server that anchors file hashes to the Bitcoin blockchain via OpenTimestamps, providing tools to anchor files, folders, and AI outputs. |
| [tbxark/mcp-proxy](https://github.com/tbxark/mcp-proxy) | [63/100](SCORES.md#tbxarkmcp-proxy) ⚠ | 735 (+7/wk) | An MCP proxy server that aggregates multiple MCP resource servers behind a single HTTP server. |
| [worklittle/jobs-mcp](https://github.com/worklittle/jobs-mcp) | [59/100](SCORES.md#worklittlejobs-mcp) | 0 | A remote MCP server that provides job search and application tools via the Worklittle platform. |

## How This Works

This registry is automatically maintained by a [GitHub Actions workflow](.github/workflows/auto-scanner.yml) that runs weekly:

1. **Discover** — searches GitHub and the [Official MCP Registry](https://registry.modelcontextprotocol.io/) for new servers; community [nominations](CONTRIBUTING.md) join the same queue
2. **Analyze** — each repo is evaluated by AI (DeepSeek-V4.1-Flash via the [DeepSeek API](https://api-docs.deepseek.com/)) on an anchored rubric, informed by deterministic scanner evidence (MCP SDK dependencies found in the repo's manifests). Prompt-injection attempts are flagged and penalized
3. **Score** — a transparent 0-100 trust score: 35% AI rubric + 65% verifiable metrics (maintenance, popularity, docs, security posture, community). The exact formula is published in [METHODOLOGY.md](METHODOLOGY.md); every server's breakdown is in [SCORES.md](SCORES.md)
4. **Re-evaluate** — the AI re-judges servers every ~90 days; metrics and trust scores refresh every week. Projects that stagnate fall off the list
5. **Rank** — only servers scoring 50+/100 appear here, top 20 per category, sorted by trust then stars
6. **Exclude** — a small human-maintained [exclusion list](data/excluded-repos.txt) overrides the AI only for spam/scam removals and maintainer opt-outs (see [CONTRIBUTING.md](CONTRIBUTING.md))

> **Model history:** until August 2026 servers were judged by GPT-4.1-mini via GitHub Models, which GitHub [shut down on July 30, 2026](https://github.blog/changelog/2026-07-30-github-models-is-now-retired) ([#36](https://github.com/sunnamed434/awesome-mcp-registry/issues/36)). From August 2026 the judge was DeepSeek-V4-Flash; since September 2026 it is DeepSeek-V4.1-Flash.

Servers are curated entirely by AI — they earn their spot through quality and lose it if they fall behind. Maintainers don't hand-pick entries. Every automated change lands as an auto-merged pull request, so the full history stays auditable and revertable.

## A Note on Security

Trust scores are computed from public metadata, the README, and [OpenSSF Scorecard](https://scorecard.dev/) data. Every entry's source is additionally scanned — **read, never executed** — for tool-poisoning markers (hidden instructions aimed at the model inside tool descriptions; flagged entries lose points in [SCORES.md](SCORES.md)). Entries are keyed by GitHub's immutable repository id, so renames are followed and a known name silently re-registered by someone else (repojacking) is quarantined instead of trusted. **Still: no entry has been code-audited or executed by this registry.** A high score means strong public signals, not a security guarantee — review any MCP server (and the credentials you grant it) before connecting it to your tools.

## Badges

Maintain a listed server? Embed your live trust score — it updates weekly and the URL survives repo renames (keyed by immutable repository id):

`![MCP trust score](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/sunnamed434/awesome-mcp-registry/master/badges/<repo_id>.json)`

Your exact copy-paste snippet is under your entry in [SCORES.md](SCORES.md).

## Contributing

**Don't open a pull request to add a server.** This README is generated from [`data/known_servers.json`](data/known_servers.json) on every run, so edits to it are overwritten — and such PRs are closed automatically.

To suggest a server, [open a nomination](https://github.com/sunnamed434/awesome-mcp-registry/issues/new?template=server-nomination.yml). The same AI evaluates it on the next weekly run and posts the verdict; if it scores 50+/100 it appears here automatically.

Code contributions (bug fixes, scanner improvements) are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). If an AI agent is contributing on your behalf, give it [AGENTS.md](AGENTS.md).
