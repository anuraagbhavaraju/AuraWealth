"""Guardrails, agent identity, audit records, and advisor-review tasks."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "advisor.db"
AGENTS = {"on_demand_insights": "agent.insights.v1", "scenario_testing": "agent.scenario.v1", "goal_planning": "agent.goal.v1"}
BLOCKED = ("ignore previous instructions", "forget all previous instructions", "forget previous instructions", "system prompt", "other client's data", "another client's data", "password", "credential", "api key", "secret key")
ESCALATE = ("move $", "transfer", "buy ", "sell ", "invest ", "advisor review", "manager", "speak to an advisor")

def connection():
    con = sqlite3.connect(DB)
    con.execute("create table if not exists advisor_tasks (id integer primary key, client_id text, agent_id text, request text, status text, created_at text)")
    return con

def guardrail(query):
    q = query.lower()
    return next((item for item in BLOCKED if item in q), None)

def should_escalate(query): return any(item in query.lower() for item in ESCALATE)

def create_task(client_id, agent_id, request):
    con = connection(); con.execute("insert into advisor_tasks (client_id,agent_id,request,status,created_at) values (?,?,?,?,?)", (client_id, agent_id, request, "Needs review", datetime.now(timezone.utc).isoformat())); con.commit(); con.close()

def tasks():
    con = connection(); rows = con.execute("select client_id,agent_id,request,status,created_at from advisor_tasks order by id desc").fetchall(); con.close(); return rows
