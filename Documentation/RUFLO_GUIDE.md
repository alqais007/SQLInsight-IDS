# Ruflo Guide — installing & driving the swarm

[ruflo](https://github.com/ruvnet/ruflo) is an agent-orchestration platform for
Claude Code (the successor to *Claude-Flow*). It lets you deploy coordinated
multi-agent **swarms**, share context through persistent **memory**, and automate
guardrails through **hooks**. This guide covers installing it and using it to
build/extend SQLInsight. For the design (topology, roster, task DAG) see
[`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).

> You do **not** need ruflo to run SQLInsight — the app is plain Python + a
> pre-built React bundle (see [`DEPLOYMENT_MAC.md`](DEPLOYMENT_MAC.md)). Ruflo is
> the *development* orchestration layer used to build it and to extend it.

---

## 1. Prerequisites

- macOS (or Linux / WSL / Git-Bash)
- Node.js 18+ and npm
- Claude Code CLI (`claude`) installed and authenticated

## 2. Install

```bash
# Quick installer (POSIX shells)
curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/ruflo@main/scripts/install.sh | bash

# …or via npm
npm install -g ruflo@latest

# …or interactive wizard
npx ruflo@latest init wizard
```

Initialize ruflo in the project:

```bash
cd /path/to/SQLInsight
npx ruflo@latest init
```

## 3. Register the MCP server with Claude Code

```bash
claude mcp add ruflo -- npx ruflo@latest mcp start
```

This exposes ruflo's MCP tools inside Claude Code, including:

| MCP tool | Purpose |
|---|---|
| `swarm_init` | create a swarm with a topology + max agents |
| `agent_spawn` | spawn a specialized agent with a task |
| `memory_store` / `memory_search` | persist & retrieve shared context (AgentDB vector store) |
| `hooks_route` | route/guard agent actions (pre/post edit, commit) |
| `swarm_status` | inspect running agents and progress |

## 4. (Optional) install plugins from the marketplace

Inside Claude Code:

```
/plugin marketplace add ruvnet/ruflo
/plugin install ruflo-core@ruflo
/plugin install ruflo-swarm@ruflo
/plugin install ruflo-rag-memory@ruflo
```

- **ruflo-core** — orchestration primitives (swarm, workflows, autopilot)
- **ruflo-swarm** — multi-agent swarm coordination
- **ruflo-rag-memory** — vector memory / RAG over the codebase

## 5. Bring up the SQLInsight swarm

The committed config in [`../ruflo/`](../ruflo/) encodes the roster + task DAG:

```bash
bash ruflo/bootstrap.sh          # issues swarm_init + memory_store + agent_spawn …
ruflo swarm status               # watch progress
```

What `bootstrap.sh` does (CLI form):

```bash
ruflo swarm init --topology hierarchical --max-agents 8 --name sqlinsight
ruflo memory store --key contract/api     --file ruflo/contracts/api.json
ruflo memory store --key contract/metrics --file ml/artifacts/metrics.json
ruflo agent spawn ml-developer  --task-file ruflo/agents/ml-engineer.md
ruflo agent spawn backend-dev   --task-file ruflo/agents/backend-engineer.md
ruflo agent spawn frontend-dev  --task-file ruflo/agents/frontend-engineer.md
ruflo agent spawn api-docs      --task-file ruflo/agents/docs-writer.md
ruflo agent spawn security-manager --task-file ruflo/agents/security-reviewer.md
ruflo agent spawn tester        --task-file ruflo/agents/integrator-qa.md
```

## 6. Driving it from natural language (Goal Planner)

ruflo also exposes a Goal-Oriented planner (GOAP + A*). Inside Claude Code you
can simply say:

> "Use the ruflo swarm in `ruflo/swarm.config.json` to add XSS detection
> alongside SQLi: extend the model, add an `/api/scan` field, and surface it on
> the dashboard."

The queen decomposes the goal, assigns it to the `ml-developer`, `backend-dev`,
and `frontend-dev` agents, and merges the result — the same flow used to build
the project.

## 7. Verifying & memory

- `ruflo verify` — cryptographic verification of the run (proof system).
- `ruflo memory search --query "api contract"` — recall stored context across
  sessions, so a later swarm picks up exactly where this one left off.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `claude mcp add` shows ruflo "failed" | ensure Node 18+, retry `npx ruflo@latest mcp start` manually to see logs |
| agents edit files outside their lane | enable the `pre-edit` hook in `ruflo/swarm.config.json` |
| swarm can't find contracts | run `memory_store` for `contract/api` and `contract/metrics` before spawning |
| want fewer agents | lower `--max-agents` or spawn only the agents you need |
