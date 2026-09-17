import unittest

from aurawealth.agents.router import answer_query
from aurawealth.data import load_client_data


class OnDemandInsightsTests(unittest.TestCase):
    def test_subscription_query_routes_to_insights_agent(self):
        result = answer_query(
            "How much did I spend on subscription services this quarter compared to last?",
            load_client_data(),
            classifier=lambda _: "on_demand_insights",
            retriever=lambda _: [],
        )

        self.assertEqual(result["route"], "on_demand_insights")
        self.assertEqual(result["insight"].prior_total, 171)
        self.assertEqual(result["insight"].current_total, 207)
        self.assertEqual(result["insight"].change, 36)
        self.assertIn("increased by $36", result["response"])

    def test_router_preserves_future_specialist_intents(self):
        result = answer_query(
            "What if I make an extra mortgage payment?",
            load_client_data(),
            classifier=lambda _: "scenario_testing",
            retriever=lambda _: [],
        )

        self.assertEqual(result["route"], "scenario_testing")
        self.assertEqual(result["route"], "scenario_testing")
        self.assertIn("interest", result["response"])
        self.assertGreater(result["scenario"]["interest_saved"], 0)

    def test_goal_planning_preserves_emergency_fund(self):
        result = answer_query("Can I afford a $6,000 holiday in December while keeping my emergency fund at $15,000?", load_client_data(), classifier=lambda _: "goal_planning", retriever=lambda _: [])
        self.assertTrue(result["goal_plan"]["affordable"])
        self.assertEqual(result["goal_plan"]["buffer"], 1300)
