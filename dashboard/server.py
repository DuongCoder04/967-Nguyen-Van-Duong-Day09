import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [dashboard] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="A2A Dashboard")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:10000")

HERE = Path(__file__).parent
HTML = (HERE / "index.html").read_text(encoding="utf-8")

# In-memory conversation history
conversations: dict[str, dict[str, Any]] = {}
MAX_HISTORY = 50

FLOW_STEPS = [
    {"id": "customer", "label": "Customer Agent receives", "agent": "Customer Agent"},
    {"id": "customer_delegate", "label": "Customer Agent → Law Agent (A2A)", "agent": "Customer Agent"},
    {"id": "law_analyze", "label": "Law Agent: analyzing & routing", "agent": "Law Agent"},
    {"id": "law_tax", "label": "Law Agent → Tax Agent (parallel)", "agent": "Law Agent"},
    {"id": "law_compliance", "label": "Law Agent → Compliance Agent (parallel)", "agent": "Law Agent"},
    {"id": "tax_process", "label": "Tax Agent: analyzing tax law...", "agent": "Tax Agent"},
    {"id": "compliance_process", "label": "Compliance Agent: analyzing regulations...", "agent": "Compliance Agent"},
    {"id": "aggregate", "label": "Law Agent: aggregating results", "agent": "Law Agent"},
    {"id": "customer_response", "label": "Customer Agent: formatting response", "agent": "Customer Agent"},
    {"id": "done", "label": "Complete", "agent": ""},
]

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML

@app.get("/api/ping")
async def ping():
    return {"status": "ok"}

@app.get("/api/health")
async def api_health():
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"{REGISTRY_URL}/health")
            return r.json()
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/agents")
async def api_agents():
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"{REGISTRY_URL}/agents")
            data = r.json()
            agents = data.get("agents", [])
            for a in agents:
                ep = a.get("endpoint", "")
                try:
                    h = await c.get(f"{ep}/.well-known/agent.json", timeout=2.0)
                    card = h.json()
                    a["name"] = card.get("name", a["agent_name"])
                    a["description"] = card.get("description", "")
                except Exception:
                    a["name"] = a["agent_name"]
            return {"agents": agents}
    except Exception as e:
        return {"agents": [], "detail": str(e)}

@app.get("/api/history")
async def api_history():
    """Return recent conversation history."""
    items = []
    for tid, conv in sorted(conversations.items(), key=lambda x: x[1].get("timestamp", ""), reverse=True)[:20]:
        items.append({
            "trace_id": tid,
            "question": conv.get("question", "")[:80],
            "timestamp": conv.get("timestamp", ""),
            "elapsed": conv.get("elapsed", 0),
        })
    return {"history": items}

@app.get("/api/history/{trace_id}")
async def api_history_detail(trace_id: str):
    conv = conversations.get(trace_id)
    if not conv:
        return JSONResponse({"error": "not found"}, status_code=404)
    return conv

_cancel_events: dict[str, asyncio.Event] = {}

@app.post("/api/cancel/{trace_id}")
async def api_cancel(trace_id: str):
    ev = _cancel_events.get(trace_id)
    if ev:
        ev.set()
        return {"status": "cancelled"}
    return {"status": "no_active_query"}

async def stream_flow(trace_id: str, question: str):
    start_time = time.time()
    cancel_ev = asyncio.Event()
    _cancel_events[trace_id] = cancel_ev

    response_text = ""
    real_elapsed = 0.0
    cancelled = False
    step_times: list[dict] = []

    async def do_real_query():
        nonlocal response_text, real_elapsed, cancelled
        ts = time.time()
        try:
            async with httpx.AsyncClient(timeout=600.0) as http_client:
                card_url = "http://localhost:10100/.well-known/agent.json"
                card_resp = await http_client.get(card_url)
                card_resp.raise_for_status()
                from a2a.types import AgentCard
                agent_card = AgentCard.model_validate(card_resp.json())
                from a2a.client import A2AClient
                from a2a.types import Message, MessageSendParams, Part, Role, SendMessageRequest, TextPart
                client = A2AClient(httpx_client=http_client, agent_card=agent_card)
                message = Message(
                    role=Role.user,
                    parts=[Part(root=TextPart(text=question))],
                    message_id=str(uuid.uuid4()),
                    metadata={"trace_id": trace_id},
                )
                request = SendMessageRequest(
                    id=str(uuid.uuid4()),
                    params=MessageSendParams(message=message),
                )
                response = await client.send_message(request)
                real_elapsed = time.time() - ts

                def _extract_text(part) -> str:
                    p = part.root if hasattr(part, "root") else part
                    return getattr(p, "text", "")

                if hasattr(response, "root"):
                    root = response.root
                    if hasattr(root, "result"):
                        result = root.result
                        # Prefer artifacts (used on successful completion)
                        if hasattr(result, "artifacts") and result.artifacts:
                            for artifact in result.artifacts:
                                for part in artifact.parts:
                                    response_text += _extract_text(part)
                        # Fallback: extract from status.message (used on failure or direct reply)
                        if not response_text and hasattr(result, "status") and result.status:
                            msg = getattr(result.status, "message", None)
                            if msg and hasattr(msg, "parts"):
                                for part in msg.parts:
                                    response_text += _extract_text(part)
                        # Last resort: if result is a Message directly
                        if not response_text and hasattr(result, "parts"):
                            for part in result.parts:
                                response_text += _extract_text(part)
        except Exception as e:
            real_elapsed = time.time() - ts
            response_text = f"[Error: {e}]"

    task = asyncio.create_task(do_real_query())

    # Estimate durations per step for the simulation (real total is unknown)
    total_estimate = 20.0
    step_weights = [1.0, 1.5, 3.0, 2.0, 2.0, 4.0, 4.0, 2.0, 1.0, 0.0]
    total_weight = sum(w for w in step_weights if w > 0)
    estimated_end = start_time + total_estimate

    for idx, step in enumerate(FLOW_STEPS):
        if cancel_ev.is_set():
            cancelled = True
            break

        step_start = time.time()
        elapsed_since_start = round(step_start - start_time, 1)
        duration_estimate = step_weights[idx]

        step_info = {
            "step": step["id"],
            "label": step["label"],
            "agent": step["agent"],
            "elapsed": elapsed_since_start,
            "duration": duration_estimate,
        }
        step_times.append(step_info)

        yield f"data: {json.dumps({'type': 'step', **step_info})}\n\n"

        if step["id"] == "done":
            await task
            if cancel_ev.is_set():
                cancelled = True
            final_elapsed = round(time.time() - start_time, 1)
            yield f"data: {json.dumps({'type': 'step', 'step': 'done', 'label': 'Complete', 'agent': '', 'elapsed': final_elapsed, 'duration': 0})}\n\n"
            yield f"data: {json.dumps({'type': 'result', 'content': response_text if not cancelled else '[Cancelled]', 'elapsed': final_elapsed, 'real_elapsed': round(real_elapsed, 1), 'cancelled': cancelled, 'steps': step_times})}\n\n"
            break

        await asyncio.sleep(min(duration_estimate, 0.5))

    if cancelled:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        final_elapsed = round(time.time() - start_time, 1)
        yield f"data: {json.dumps({'type': 'result', 'content': '[Cancelled by user]', 'elapsed': final_elapsed, 'real_elapsed': 0, 'cancelled': True, 'steps': step_times})}\n\n"

    # Store in history
    conversations[trace_id] = {
        "trace_id": trace_id,
        "question": question,
        "response": response_text if not cancelled else "[Cancelled]",
        "elapsed": round(real_elapsed, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_time)),
        "steps": step_times,
        "cancelled": cancelled,
    }
    if len(conversations) > MAX_HISTORY:
        oldest = sorted(conversations.keys(), key=lambda k: conversations[k].get("timestamp", ""))[0]
        conversations.pop(oldest, None)

    _cancel_events.pop(trace_id, None)
    yield "data: [DONE]\n\n"

@app.post("/api/query")
async def api_query(request: Request):
    body = await request.json()
    question = body.get("question", "")
    trace_id = body.get("trace_id", str(uuid.uuid4()))
    if not question:
        return JSONResponse({"error": "question required"}, status_code=400)

    return StreamingResponse(
        stream_flow(trace_id, question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", "10420"))
    logger.info("Dashboard server: http://localhost:%d", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
