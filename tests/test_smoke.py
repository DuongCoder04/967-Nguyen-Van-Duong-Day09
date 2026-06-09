from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from langchain_core.messages import AIMessage, ToolMessage

from common.a2a_client import _extract_text
from customer_agent.agent_executor import _extract_answer
from exercises.exercise_4_multiagent import (
    build_graph as build_exercise_graph,
    check_routing as exercise_routing,
)
from law_agent.graph import create_graph as create_law_graph
from law_agent.graph_optimized import create_graph as create_optimized_law_graph
from registry.__main__ import AgentRegistration, agents, discover, register
from stages.stage_4_milti_agent.main import (
    create_graph as create_stage_4_graph,
    route_to_specialists,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        agents.clear()

    async def test_register_and_discover_agent(self) -> None:
        registration = AgentRegistration(
            agent_name="Tax Agent",
            endpoint="http://localhost:10102",
            tasks=["tax_question"],
        )

        response = await register(registration)
        discovered = await discover("tax_question")

        self.assertEqual(response["status"], "ok")
        self.assertEqual(discovered["agent_name"], "Tax Agent")
        self.assertEqual(discovered["endpoint"], "http://localhost:10102")

    async def test_discover_unknown_task_returns_404(self) -> None:
        with self.assertRaises(HTTPException) as context:
            await discover("missing_task")

        self.assertEqual(context.exception.status_code, 404)


class GraphTests(unittest.TestCase):
    def test_all_state_graphs_compile(self) -> None:
        graph_factories = [
            create_law_graph,
            create_optimized_law_graph,
            create_stage_4_graph,
            build_exercise_graph,
        ]

        for factory in graph_factories:
            with self.subTest(factory=factory.__module__):
                self.assertIsNotNone(factory())

    def test_stage_4_routes_to_requested_specialists(self) -> None:
        routes = route_to_specialists(
            {
                "needs_tax": True,
                "needs_compliance": True,
            }
        )

        self.assertEqual(
            {route.node for route in routes},
            {"call_tax_specialist", "call_compliance_specialist"},
        )

    def test_exercise_routes_privacy_questions(self) -> None:
        routes = exercise_routing(
            {
                "question": "Công ty bị rò rỉ dữ liệu khách hàng",
            }
        )

        self.assertEqual([route.node for route in routes], ["privacy_agent"])

    def test_stage_4_routes_directly_to_aggregate_when_no_specialist_needed(self) -> None:
        routes = route_to_specialists(
            {
                "needs_tax": False,
                "needs_compliance": False,
            }
        )

        self.assertEqual([route.node for route in routes], ["aggregate"])


class CustomerResponseTests(unittest.TestCase):
    def test_prefers_delegated_specialist_response(self) -> None:
        messages = [
            ToolMessage(
                content="Full specialist analysis",
                name="delegate_to_legal_agent",
                tool_call_id="call-1",
            ),
            AIMessage(content="Short disclaimer"),
        ]

        self.assertEqual(_extract_answer(messages), "Full specialist analysis")

    def test_uses_ai_message_without_delegation(self) -> None:
        self.assertEqual(
            _extract_answer([AIMessage(content="Direct response")]),
            "Direct response",
        )


class A2AResponseTests(unittest.TestCase):
    def test_extracts_text_from_task_artifacts(self) -> None:
        response = SimpleNamespace(
            root=SimpleNamespace(
                result=SimpleNamespace(
                    artifacts=[
                        SimpleNamespace(
                            parts=[
                                SimpleNamespace(
                                    root=SimpleNamespace(text="Legal analysis")
                                )
                            ]
                        )
                    ]
                )
            )
        )

        self.assertEqual(_extract_text(response), "Legal analysis")

    def test_falls_back_to_task_history(self) -> None:
        response = SimpleNamespace(
            result=SimpleNamespace(
                artifacts=[],
                parts=[],
                history=[
                    SimpleNamespace(
                        parts=[SimpleNamespace(root=SimpleNamespace(text="Fallback"))]
                    )
                ],
            )
        )

        self.assertEqual(_extract_text(response), "Fallback")

    def test_returns_empty_text_for_unsuccessful_response(self) -> None:
        self.assertEqual(_extract_text(SimpleNamespace(result=None)), "")


class DelegationFailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_law_agent_returns_unavailable_message_when_discovery_fails(self) -> None:
        from law_agent.graph import call_tax

        state = {
            "question": "Tax question",
            "context_id": "context",
            "trace_id": "trace",
            "delegation_depth": 1,
        }
        with patch(
            "common.registry_client.discover",
            new=AsyncMock(side_effect=RuntimeError("registry unavailable")),
        ):
            result = await call_tax(state)

        self.assertIn("Tax analysis unavailable", result["tax_result"])


class RegistrationFailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_agent_fails_fast_when_registry_never_accepts_registration(self) -> None:
        from customer_agent.__main__ import _register_with_retry

        with patch(
            "customer_agent.__main__.register",
            new=AsyncMock(side_effect=RuntimeError("registry unavailable")),
        ):
            with self.assertRaisesRegex(RuntimeError, "could not register"):
                await _register_with_retry(max_attempts=1, delay=0)


class DocumentationTests(unittest.TestCase):
    def test_readme_local_links_exist(self) -> None:
        content = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", content)
        local_targets = [
            target.split("#", 1)[0]
            for target in targets
            if target and not target.startswith(("http://", "https://", "#"))
        ]

        missing = [
            target
            for target in local_targets
            if not (PROJECT_ROOT / target).exists()
        ]
        self.assertEqual(missing, [])

    def test_exercise_templates_exist(self) -> None:
        expected = [
            "exercises/templates/exercise_2_tools.py.template",
            "exercises/templates/exercise_4_multiagent.py.template",
            "exercises/SOLUTIONS.md",
        ]
        self.assertTrue(all((PROJECT_ROOT / path).is_file() for path in expected))


if __name__ == "__main__":
    unittest.main()
