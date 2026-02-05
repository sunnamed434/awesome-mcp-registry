# Awesome MCP Registry

![Servers](https://img.shields.io/badge/servers-26-blue) ![Categories](https://img.shields.io/badge/categories-8-green) ![Avg Quality](https://img.shields.io/badge/avg%20quality-8.1%2F10-orange) ![Updated](https://img.shields.io/badge/updated-2026-02-05-lightgrey) ![Auto-curated](https://img.shields.io/badge/curated%20by-AI-purple)

An AI-powered, self-updating directory of [Model Context Protocol](https://modelcontextprotocol.io/) servers. Discovered from GitHub and the [Official MCP Registry](https://registry.modelcontextprotocol.io/), analyzed and rated by AI weekly.

## Stats

- **Total servers:** 26
- **Categories:** 8
- **Avg quality:** 8.1/10

## Databases (2)

| Server | Stars | Quality | Description |
|--------|-------|---------|-------------|
| [mindsdb/mindsdb](https://github.com/mindsdb/mindsdb) | 38403 | 8/10 | MindsDB is a federated query engine for AI. |
| [googleapis/genai-toolbox](https://github.com/googleapis/genai-toolbox) | 12733 | 8/10 | An open source MCP server for databases. |

## Dev Tools (14)

| Server | Stars | Quality | Description |
|--------|-------|---------|-------------|
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | 26664 | 9/10 | GitHub's official MCP Server for AI tool integration. |
| [upstash/context7](https://github.com/upstash/context7) | 44839 | 8/10 | Context7 MCP Server for up-to-date code documentation. |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 26723 | 8/10 | A Model Context Protocol server for browser automation using Playwright. |
| [jlowin/fastmcp](https://github.com/jlowin/fastmcp) | 22626 | 8/10 | FastMCP is a Python framework for building MCP servers and applications. |
| [oraios/serena](https://github.com/oraios/serena) | 19754 | 8/10 | A coding agent toolkit providing semantic retrieval and editing capabilities. |
| [BeehiveInnovations/pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server) | 11007 | 8/10 | A CLI tool that orchestrates multiple AI models for enhanced workflows. |
| [hangwin/mcp-chrome](https://github.com/hangwin/mcp-chrome) | 10278 | 8/10 | Chrome extension-based MCP server for browser automation and AI integration. |
| [idosal/git-mcp](https://github.com/idosal/git-mcp) | 7527 | 8/10 | GitMCP is a remote MCP server for GitHub projects that enhances AI tool access to documentation. |
| [LaurieWired/GhidraMCP](https://github.com/LaurieWired/GhidraMCP) | 7286 | 8/10 | MCP Server for Ghidra enabling autonomous reverse engineering. |
| [wonderwhy-er/DesktopCommanderMCP](https://github.com/wonderwhy-er/DesktopCommanderMCP) | 5399 | 8/10 | MCP server for terminal control and file management. |
| [executeautomation/mcp-playwright](https://github.com/executeautomation/mcp-playwright) | 5207 | 8/10 | A Model Context Protocol server for browser automation using Playwright. |
| [cameroncooke/XcodeBuildMCP](https://github.com/cameroncooke/XcodeBuildMCP) | 4110 | 8/10 | An MCP server and CLI for iOS and macOS project tools. |
| [mobile-next/mobile-mcp](https://github.com/mobile-next/mobile-mcp) | 3322 | 8/10 | MCP server for mobile automation and scraping across platforms. |
| [BrowserMCP/mcp](https://github.com/BrowserMCP/mcp) | 5701 | 7/10 | Browser MCP is an MCP server that automates browser tasks using AI. |

## Cloud (1)

| Server | Stars | Quality | Description |
|--------|-------|---------|-------------|
| [awslabs/mcp](https://github.com/awslabs/mcp) | 8064 | 9/10 | A suite of specialized MCP servers for AWS. |

## Productivity (1)

| Server | Stars | Quality | Description |
|--------|-------|---------|-------------|
| [Pimzino/spec-workflow-mcp](https://github.com/Pimzino/spec-workflow-mcp) | 3839 | 8/10 | A productivity-focused MCP server for structured spec-driven development. |

## Communication (1)

| Server | Stars | Quality | Description |
|--------|-------|---------|-------------|
| [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) | 5298 | 8/10 | WhatsApp MCP server for managing messages and media. |

## Web Scraping (1)

| Server | Stars | Quality | Description |
|--------|-------|---------|-------------|
| [firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server) | 5414 | 9/10 | Official Firecrawl MCP Server for web scraping and search. |

## AI & ML (5)

| Server | Stars | Quality | Description |
|--------|-------|---------|-------------|
| [activepieces/activepieces](https://github.com/activepieces/activepieces) | 20741 | 8/10 | Activepieces is an AI automation platform with extensible MCP servers. |
| [GLips/Figma-Context-MCP](https://github.com/GLips/Figma-Context-MCP) | 13005 | 8/10 | MCP server providing Figma data to AI coding agents. |
| [kreuzberg-dev/kreuzberg](https://github.com/kreuzberg-dev/kreuzberg) | 5737 | 8/10 | A polyglot document intelligence framework for extracting information from various file formats. |
| [u14app/deep-research](https://github.com/u14app/deep-research) | 4372 | 8/10 | A server for generating in-depth research reports using various LLMs. |
| [mcp-use/mcp-use](https://github.com/mcp-use/mcp-use) | 9091 | 7/10 | mcp-use provides tools to build MCP servers and clients easily. |

## Security (1)

| Server | Stars | Quality | Description |
|--------|-------|---------|-------------|
| [0x4m4/hexstrike-ai](https://github.com/0x4m4/hexstrike-ai) | 6653 | 9/10 | HexStrike AI MCP Agents is an advanced MCP server for automated cybersecurity tools. |

## How This Works

This registry is automatically maintained by a [GitHub Actions workflow](.github/workflows/auto-scanner.yml) that runs weekly:

1. **Discover** — searches GitHub and the [Official MCP Registry](https://registry.modelcontextprotocol.io/) for new servers
2. **Analyze** — each new repo is evaluated by AI (GPT-4o-mini via [GitHub Models](https://docs.github.com/en/github-models))
3. **Re-evaluate** — servers older than 90 days are re-analyzed with fresh data. If a project is abandoned, loses quality, or stops being relevant, its score drops and it falls off the list
4. **Rank** — only servers scoring 5+/10 appear here, top 20 per category, sorted by quality then stars

No manual curation, no PRs. Servers earn their spot through quality — and lose it if they fall behind.
