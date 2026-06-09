"""End-to-end test client for the Legal Multi-Agent System.

Sends a legal question to the Customer Agent and prints the response.
"""

import asyncio
import argparse
import os
import sys
import time
from uuid import uuid4

import httpx
from dotenv import load_dotenv

from common.a2a_client import _extract_text

load_dotenv()

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")
A2A_TIMEOUT_SECONDS = float(os.getenv("A2A_TIMEOUT_SECONDS", "300"))

QUESTION = (
    "If a company breaks a contract and avoids taxes, "
    "what are the legal and regulatory consequences?"
)


async def main(question: str) -> None:
    trace_id = str(uuid4())
    print(f"Connecting to Customer Agent at {CUSTOMER_AGENT_URL}")
    print(f"Trace ID: {trace_id}")
    print(f"Question: {question}")
    print("-" * 60)

    async with httpx.AsyncClient(timeout=A2A_TIMEOUT_SECONDS) as http_client:
        # Resolve agent card
        card_url = f"{CUSTOMER_AGENT_URL}/.well-known/agent.json"
        try:
            card_resp = await http_client.get(card_url)
            card_resp.raise_for_status()
        except Exception as e:
            print(f"ERROR: Could not reach Customer Agent at {card_url}")
            print(f"  {e}")
            print("Make sure all services are running (./start_all.sh)")
            sys.exit(1)

        from a2a.types import AgentCard, Message, Part, Role, TextPart
        from a2a.client import A2AClient

        agent_card = AgentCard.model_validate(card_resp.json())
        print(f"Connected to agent: {agent_card.name} v{agent_card.version}")
        print("-" * 60)

        # Build the legacy A2AClient
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        # Construct the message
        from a2a.types import SendMessageRequest, MessageSendParams as MSP
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=question))],
            message_id=str(uuid4()),
            metadata={"trace_id": trace_id},
        )
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MSP(message=message),
        )

        print("Sending request (this may take 30-60s while agents chain)...\n")
        started_at = time.perf_counter()
        response = await client.send_message(request)
        elapsed = time.perf_counter() - started_at
        result_text = _extract_text(response)

        if result_text:
            print("RESPONSE:")
            print("=" * 60)
            print(result_text)
            print("=" * 60)
            print(f"Elapsed: {elapsed:.1f}s")
        else:
            print("No text response received. Raw response:")
            print(response)
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", default=QUESTION)
    args = parser.parse_args()
    asyncio.run(main(args.question))
