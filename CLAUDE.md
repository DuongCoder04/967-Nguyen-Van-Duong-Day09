# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A distributed legal advisory system built as a teaching codelab. Five agents communicate via Google's A2A protocol, managed with LangGraph and LangChain, using OpenRouter as the LLM provider. The `stages/` folder contains progressive standalone demos (Stage 1–4); the root-level agent packages (Stage 5) form the full distributed system.

## Commands

```bash
# Install dependencies
uv sync

# Run the full distributed system (all 5 services)
./start_all.sh

# Send a test query to the running system
uv run python test_client.py

# Run individual stage demos (no servers needed)
uv run python stages/stage_1_direct_llm/main.py
uv run python stages/stage_2_rag_tools/main.py
uv run python stages/stage_3_single_agent/main.py
uv run python stages/stage_4_milti_agent/main.py   # note: typo in folder name

# Run individual agents (Stage 5)
uv run python -m registry        # port 10000 — start first
uv run python -m tax_agent       # port 10102
uv run python -m compliance_agent # port 10103
uv run python -m law_agent       # port 10101
uv run python -m customer_agent  # port 10100

# Debug a stuck port
lsof -i :10000
kill -9 <PID>

# Reinstall if dependencies break
rm -rf .venv && uv sync
```

## Environment

Copy `.env.example` to `.env` and set:
- `OPENROUTER_API_KEY` — required, get from openrouter.ai
- `OPENROUTER_MODEL` — defaults to `nhà cung cấp dịch vụ AI/claude-opus-4.7`
- `REGISTRY_URL` — defaults to `http://localhost:10000`

## Architecture

### Stage 5 — Distributed A2A System

```
Registry (10000)  ←  all agents self-register on startup
      ↓
Customer Agent (10100)  ←  user entry point, uses create_react_agent
      ↓
Law Agent (10101)  ←  custom StateGraph orchestrator
      ↓  (parallel via LangGraph Send API)
Tax Agent (10102)        Compliance Agent (10103)
  create_react_agent       create_react_agent
```

**Request flow:** User → Customer Agent detects legal domain → delegates to Law Agent via A2A → Law Agent runs `analyze_law`, then `check_routing` (LLM decides if tax/compliance needed), then dispatches `call_tax` and `call_compliance` in parallel → `aggregate` synthesizes all results → response returns up the chain.

### Agent module structure (same for all 4 agents)

- `graph.py` — LangGraph graph definition with all agent logic
- `agent_executor.py` — bridge between A2A SDK and LangGraph (`AgentExecutor` subclass)
- `__main__.py` — server bootstrap: registers with Registry, builds `AgentCard`, starts uvicorn

### Shared utilities (`common/`)

- `llm.py` — `get_llm()` returns a `ChatOpenAI` pointed at OpenRouter
- `registry_client.py` — `discover(task)` and `register(info)` async helpers
- `a2a_client.py` — `delegate(endpoint, question, context_id, trace_id, depth)` sends A2A messages and extracts text from the response tree

### Key patterns

- **Dynamic discovery:** agents call `discover("tax_question")` at runtime; no hardcoded URLs between agents
- **Parallel branches:** `LawState` uses `Annotated[str, _last_wins]` on `tax_result` and `compliance_result` so both parallel `Send` branches can write without conflict
- **Depth guard:** `MAX_DELEGATION_DEPTH = 3` in `law_agent/graph.py` prevents infinite loops
- **Trace propagation:** `trace_id` and `context_id` are threaded through every A2A hop for debugging
- **Startup retry:** `__main__.py` in each agent retries registry registration with backoff until the registry is ready

### Registry

Pure FastAPI in-memory store (not a LangGraph agent). Endpoints: `POST /register`, `GET /discover/{task}`, `GET /agents`, `GET /health`. State is lost on restart — agents re-register on each startup.

## Startup Order

Registry must be up before agents register. Leaf agents (tax, compliance) before orchestrators (law, customer). `start_all.sh` handles this with `sleep` delays.
