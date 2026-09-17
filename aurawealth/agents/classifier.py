"""LLM-backed intent classification for the AuraWealth client chat."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ALLOWED_INTENTS = (
    "on_demand_insights",
    "scenario_testing",
    "goal_planning",
    "unsupported",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env.local")

CLASSIFIER_INSTRUCTIONS = """You are the routing layer for AuraWealth, a consumer wealth-management demo.
Classify the client's message into exactly one intent:
- on_demand_insights: asks for a past or current spending insight, comparison, or summary.
- scenario_testing: asks a what-if question, especially about a mortgage prepayment or financial change.
- goal_planning: asks whether a planned cost fits a savings goal, cash flow, or emergency-fund target.
- unsupported: anything else.

Do not answer the user. Return only the selected intent."""

INTENT_SCHEMA = {
    "type": "object",
    "properties": {"intent": {"type": "string", "enum": list(ALLOWED_INTENTS)}},
    "required": ["intent"],
    "additionalProperties": False,
}


def classify_intent(query: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("The OpenAI API key is not configured.")

    response = OpenAI().responses.create(
        model="gpt-5.5",
        instructions=CLASSIFIER_INSTRUCTIONS,
        input=query,
        text={
            "format": {
                "type": "json_schema",
                "name": "aurawealth_intent",
                "strict": True,
                "schema": INTENT_SCHEMA,
            }
        },
        store=False,
    )
    intent = json.loads(response.output_text)["intent"]
    if intent not in ALLOWED_INTENTS:
        raise RuntimeError("The classifier returned an invalid intent.")
    return intent
