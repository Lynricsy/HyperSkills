# NOTICE — mcp-server

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- modelcontextprotocol/modelcontextprotocol (Apache-2.0) — https://github.com/modelcontextprotocol/modelcontextprotocol @ aa8ce049f089f92618340190d4ece141f663310d — paths: schema/2026-07-28, docs/specification/2026-07-28 — Normative 2026-07-28 facts: per-request _meta envelope, server/discover, resultType, transports, tool and resource rules, authorization, pagination, caching, and the deprecated-feature registry.
- modelcontextprotocol/python-sdk (MIT) — https://github.com/modelcontextprotocol/python-sdk @ 9972c21aa42054fb1450c5fc614761ed11847ec6 — paths: src/mcp/server, src/mcp/types — Observed Python behaviour at mcp 2.2.0: MCPServer replacing FastMCP, the stdio fd-diversion guard, required _meta envelope keys, and the modern/legacy era split.
- modelcontextprotocol/typescript-sdk (Apache-2.0) — https://github.com/modelcontextprotocol/typescript-sdk @ 5ecc791d81a7221ebe15ae3ae3f36a8e978af820 — paths: packages/core, packages/server — Observed TypeScript behaviour: the v1 single-package 1.30.0 line versus the v2 scoped packages at 2.0.0, their protocol ceilings, serveStdio's factory argument, and the required JSON Schema validator.
- anthropics/claude-plugins-official (Apache-2.0) — https://github.com/anthropics/claude-plugins-official @ 3b600518a637492d37c9877aeb49c2a55d939c04 — paths: plugins/mcp-server-dev/skills/build-mcp-server, plugins/mcp-server-dev/skills/build-mcpb/references/local-security.md — Deployment-shape decision, tool description and schema-tightening rules, the three auth tiers, and the 'a local server has no sandbox, so tool arguments are untrusted input' framing with path-containment checks.
- anthropics/skills (Apache-2.0) — https://github.com/anthropics/skills @ 34040c9c568585f6929bedeaad110ad08f079624 — paths: skills/mcp-builder — Response-size budgeting with an explicit truncation marker, the rule that doc comments are not extracted into tool descriptions, and the design principles for LLM-usability evaluations of a finished server.
- github/awesome-copilot (MIT) — https://github.com/github/awesome-copilot @ 7568a482ce2df38f8965ab5336a3220db796a4ba — paths: skills/typescript-mcp-server-generator, skills/dotnet-mcp-builder, skills/mcp-implementation-security-review, skills/mcp-security-audit, skills/mcp-release-qa — TypeScript SDK v1-to-v2 package split and codemod, the .NET stateless default, the security-review baseline with its false-positive filters and bind-address truth table, pre-release runtime QA discipline, and client-configuration hygiene.
- microsoft/skills (MIT) — https://github.com/microsoft/skills @ cf77b1efbf3117501f4727c476894751311ee885 — paths: .github/skills/mcp-builder/reference/mcp_best_practices.md — Tool-annotation default table and the falsifiable acceptance bar for a tool description — it must win against sibling tools for its own intent and must not be selected for unrelated ones.

Reference-only sources (no content copied):

- modelcontextprotocol/inspector (MIT) — https://github.com/modelcontextprotocol/inspector
- cloudflare/skills (Apache-2.0) — https://github.com/cloudflare/skills
