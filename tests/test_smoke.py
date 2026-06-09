from types import SimpleNamespace
import unittest

from fastapi import HTTPException

from common.a2a_client import _extract_text
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


if __name__ == "__main__":
    unittest.main()
