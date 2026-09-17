import streamlit as st

from aurawealth.agents.router import answer_query
from aurawealth.data import client_options, load_client_data
from aurawealth.rag.library import build_index, chunk_count
from aurawealth.governance import tasks

def currency(value: float) -> str:
    return f"${value:,.0f}"


st.set_page_config(page_title="AuraWealth", page_icon="✦", layout="wide")
options = client_options()
selected_name = st.sidebar.selectbox("Demo client", [name for _, name in options])
selected_id = next(client_id for client_id, name in options if name == selected_name)
data = load_client_data(selected_id)
client = data["client"]
goal = data["goal"]
mortgage = data["mortgage"]

st.title("AuraWealth")
st.caption("A transparent view of your money, goals, and advisor support.")

with st.sidebar:
    st.subheader("Trusted knowledge library")
    st.caption("Synthetic, approved AuraWealth education content")
    st.metric("Indexed chunks", chunk_count())
    if st.button("Build semantic index"):
        with st.spinner("Embedding approved guidance..."):
            total = build_index()
        st.success(f"Indexed {total:,} chunks across 12 documents.")

client_tab, advisor_tab = st.tabs(["Client workspace", "Advisor queue"])

with client_tab:
    st.subheader(f"Good afternoon, {client['name'].split()[0]}")
    net_worth = client["cash_balance"] + client["investment_balance"] - mortgage["outstanding_balance"]
    metrics = st.columns(4)
    metrics[0].metric("Cash", currency(client["cash_balance"]))
    metrics[1].metric("Investments", currency(client["investment_balance"]))
    metrics[2].metric("Mortgage", currency(mortgage["outstanding_balance"]))
    metrics[3].metric("Net worth", currency(net_worth))

    overview, planning = st.columns([1.2, 1])
    with overview:
        st.markdown("#### Your financial snapshot")
        st.write(
            f"Your monthly income is {currency(client['monthly_income'])}. "
            f"Your mortgage payment is {currency(mortgage['monthly_payment'])} each month."
        )
        st.markdown("#### On-Demand Insights")
        st.info("Ask Aura to compare your subscription spending across quarters.")

    with planning:
        st.markdown("#### Goal: December holiday")
        st.progress(goal["saved_amount"] / goal["target_amount"])
        st.write(f"{currency(goal['saved_amount'])} of {currency(goal['target_amount'])} saved")
        st.caption(
            f"Saving {currency(goal['monthly_saving'])}/month · Target date: {goal['target_month']}"
        )
        st.write(f"Emergency-fund target: {currency(client['emergency_fund_target'])}")

    st.divider()
    st.markdown("#### Ask Aura")
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "I can compare your subscription spending this quarter with last quarter.",
            }
        ]

    for message in st.session_state.messages:
        st.chat_message(message["role"]).write(message["content"])

    prompt = st.chat_input("Ask about your finances")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        try:
            result = answer_query(prompt, data, client_id=client["id"])
            response = result["response"]
        except RuntimeError as error:
            response = f"I couldn't classify that request right now: {error}"
            result = {}
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)

        if result.get("insight"):
            insight = result["insight"]
            result_metrics = st.columns(3)
            result_metrics[0].metric(insight.current_quarter, currency(insight.current_total))
            result_metrics[1].metric(insight.prior_quarter, currency(insight.prior_total))
            result_metrics[2].metric("Change", currency(insight.change), f"{insight.change_percent:.0f}%")
        if result.get("sources"):
            st.caption("Trusted sources: " + " · ".join(source["title"] for source in result["sources"]))
        if result.get("scenario"):
            scenario = result["scenario"]
            scenario_metrics = st.columns(3)
            scenario_metrics[0].metric("Extra payment", currency(scenario["extra_payment"]))
            scenario_metrics[1].metric("Estimated interest saved", currency(scenario["interest_saved"]))
            scenario_metrics[2].metric("Loan term reduced", f"{scenario['months_saved']} months")
        if result.get("goal_plan"):
            plan = result["goal_plan"]
            goal_metrics = st.columns(3)
            goal_metrics[0].metric("Holiday cost", currency(plan["planned_cost"]))
            goal_metrics[1].metric("Cash after holiday", currency(plan["cash_after_cost"]))
            goal_metrics[2].metric("Emergency-fund buffer", currency(plan["buffer"]))
        if result.get("audit"):
            with st.expander("How Aura reached this result"):
                st.json(result["audit"])

with advisor_tab:
    st.subheader("Advisor review queue")
    queue = tasks()
    if not queue: st.info("No requests yet.")
    for client_id, agent_id, request, status, created_at in queue:
        st.write(f"**{status}** · {client_id} · {agent_id}")
        st.caption(f"{request} · {created_at}")
