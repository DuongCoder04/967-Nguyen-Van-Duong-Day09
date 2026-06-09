"""Measure end-to-end latency for the currently configured runtime.

Usage:
    # Start services first: ./start_all.sh
    uv run python benchmark.py
"""

import asyncio
import os
import time
from uuid import uuid4

import httpx
from dotenv import load_dotenv

load_dotenv()

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:10000")
A2A_TIMEOUT_SECONDS = float(os.getenv("A2A_TIMEOUT_SECONDS", "300"))
QUESTION = "If a company breaks a contract and avoids taxes, what are the legal and regulatory consequences?"

N_RUNS = int(os.getenv("BENCHMARK_RUNS", "1"))


async def run_query(label: str) -> float:
    """Send one query to Customer Agent and return elapsed seconds."""
    async with httpx.AsyncClient(timeout=A2A_TIMEOUT_SECONDS) as http_client:
        from a2a.client import A2AClient
        from a2a.types import AgentCard, Message, MessageSendParams, Part, Role, SendMessageRequest, TextPart

        card_resp = await http_client.get(f"{CUSTOMER_AGENT_URL}/.well-known/agent.json")
        card_resp.raise_for_status()
        agent_card = AgentCard.model_validate(card_resp.json())
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=QUESTION))],
            message_id=str(uuid4()),
        )
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message=message),
        )

        start = time.perf_counter()
        await client.send_message(request)
        elapsed = time.perf_counter() - start

        print(f"  [{label}] {elapsed:.1f}s")
        return elapsed


async def main():
    print("=" * 60)
    print("LATENCY BENCHMARK — Stage 5 Distributed A2A")
    print("=" * 60)
    print(f"Question: {QUESTION[:60]}...")
    print()

    # Check services are up
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{REGISTRY_URL}/health")
            r.raise_for_status()
            agents_response = await client.get(f"{REGISTRY_URL}/agents")
            agents_response.raise_for_status()
        except Exception:
            print("ERROR: Services not running. Start with ./start_all.sh")
            return

    print(f"Registry: {len(agents_response.json()['agents'])} agents registered")
    print()

    print(f"Running {N_RUNS} query(ies)...")
    times = []
    for i in range(N_RUNS):
        t = await run_query(f"run {i+1}")
        times.append(t)

    avg = sum(times) / len(times)
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  Runs:    {N_RUNS}")
    print(f"  Times:   {[f'{t:.1f}s' for t in times]}")
    print(f"  Average: {avg:.1f}s")
    print()
    print(f"Provider: {os.getenv('LLM_PROVIDER', 'openrouter')}")
    print(f"Configured end-to-end timeout: {A2A_TIMEOUT_SECONDS:.0f}s")
    print("Compare runs only when question, provider, model, and hardware are unchanged.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
