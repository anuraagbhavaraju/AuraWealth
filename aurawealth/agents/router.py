"""A small LangGraph workflow that routes to the available specialist agent."""

from collections.abc import Callable
from typing import Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from aurawealth.agents.classifier import classify_intent
from aurawealth.agents.insights import subscription_comparison
from aurawealth.calculators.mortgage import model_prepayment, prepayment_amount
from aurawealth.calculators.goals import model_goal_affordability
from aurawealth.models import InsightResult
from aurawealth.rag.library import retrieve
from aurawealth.governance import AGENTS, create_task, guardrail, should_escalate


class AgentState(TypedDict, total=False):
    query: str
    client_id: str
    client_data: dict[str, Any]
    route: str
    insight: InsightResult
    scenario: dict[str, Any]
    goal_plan: dict[str, Any]
    sources: list[dict[str, Any]]
    response: str
    agent_id: str
    audit: dict[str, Any]


def choose_route(state: AgentState, classifier: Callable[[str], str]) -> dict[str, str]:
    return {"route": classifier(state["query"])}

def preflight(state: AgentState) -> dict[str, Any]:
    blocked = guardrail(state["query"])
    if blocked: return {"route": "blocked", "response": "I can’t help with requests that bypass security or access another client’s information.", "audit": {"guardrail": blocked}}
    return {}

def govern(state: AgentState) -> dict[str, Any]:
    agent_id = AGENTS.get(state.get("route"), "agent.governance.v1")
    audit = {"client_id": state["client_id"], "agent_id": agent_id, "route": state.get("route"), "sources": state.get("sources", []), "action": "informational"}
    if should_escalate(state["query"]):
        create_task(state["client_id"], agent_id, state["query"])
        return {"agent_id": agent_id, "audit": audit, "response": "Your request has been sent to your advisor for review. No action has been taken."}
    return {"agent_id": agent_id, "audit": audit}


def run_insights(state: AgentState, retriever: Callable[[str], list]) -> dict[str, Any]:
    insight = subscription_comparison(state["client_data"])
    response = (
        f"You spent ${insight.current_total:,.0f} on subscription services in "
        f"{insight.current_quarter}, compared with ${insight.prior_total:,.0f} in "
        f"{insight.prior_quarter}. {insight.explanation}"
    )
    sources = retriever(state["query"])
    if sources:
        response += "\n\nTrusted guidance: " + ", ".join(source["title"] for source in sources)
    return {"insight": insight, "response": response, "sources": sources}


def unsupported_query(_: AgentState) -> dict[str, str]:
    return {"response": "I can currently help with your subscription spending across quarters."}


def run_scenario_testing(state: AgentState, retriever: Callable[[str], list]) -> dict[str, Any]:
    extra_payment = prepayment_amount(state["query"])
    scenario = model_prepayment(state["client_data"]["mortgage"], extra_payment)
    response = (
        f"A one-off ${scenario['extra_payment']:,.0f} mortgage prepayment could save about "
        f"${scenario['interest_saved']:,.0f} in interest and shorten the loan by "
        f"{scenario['months_saved']} months, assuming you keep the same monthly payment."
    )
    sources = retriever(state["query"])
    if sources:
        response += "\n\nTrusted guidance: " + ", ".join(source["title"] for source in sources)
    return {"scenario": scenario, "sources": sources, "response": response}


def run_goal_planning(state: AgentState, retriever: Callable[[str], list]) -> dict[str, Any]:
    plan = model_goal_affordability(state["client_data"])
    verdict = "can afford" if plan["affordable"] else "cannot afford"
    response = f"You {verdict} the ${plan['planned_cost']:,.0f} holiday while keeping your emergency fund at ${plan['emergency_fund_target']:,.0f}. Your projected cash after the trip is ${plan['cash_after_cost']:,.0f}, leaving a ${plan['buffer']:,.0f} buffer."
    sources = retriever(state["query"])
    if sources:
        response += "\n\nTrusted guidance: " + ", ".join(source["title"] for source in sources)
    return {"goal_plan": plan, "sources": sources, "response": response}


def route_after_classifier(state: AgentState) -> str:
    return state["route"]


def build_workflow(
    classifier: Callable[[str], str] = classify_intent,
    retriever: Callable[[str], list] = retrieve,
):
    workflow = StateGraph(AgentState)
    workflow.add_node("router", lambda state: choose_route(state, classifier))
    workflow.add_node("preflight", preflight)
    workflow.add_node("governance", govern)
    workflow.add_node("insights", lambda state: run_insights(state, retriever))
    workflow.add_node("scenario_testing", lambda state: run_scenario_testing(state, retriever))
    workflow.add_node("goal_planning", lambda state: run_goal_planning(state, retriever))
    workflow.add_node("unsupported", unsupported_query)
    workflow.add_edge(START, "preflight")
    workflow.add_conditional_edges("preflight", lambda s: "blocked" if s.get("route") == "blocked" else "router", {"blocked": "governance", "router": "router"})
    workflow.add_conditional_edges(
        "router",
        route_after_classifier,
        {
            "on_demand_insights": "insights",
            "scenario_testing": "scenario_testing",
            "goal_planning": "goal_planning",
            "unsupported": "unsupported",
        },
    )
    workflow.add_edge("insights", "governance")
    workflow.add_edge("scenario_testing", "governance")
    workflow.add_edge("goal_planning", "governance")
    workflow.add_edge("unsupported", "governance")
    workflow.add_edge("governance", END)
    return workflow.compile()


def answer_query(
    query: str,
    client_data: dict[str, Any],
    client_id: str = "client_001",
    classifier: Callable[[str], str] = classify_intent,
    retriever: Callable[[str], list] = retrieve,
    conversation_context: Optional[str] = None,
) -> AgentState:
    routing_classifier = lambda _: classifier(conversation_context or query)
    return build_workflow(routing_classifier, retriever).invoke(
        {"query": query, "client_data": client_data, "client_id": client_id}
    )
