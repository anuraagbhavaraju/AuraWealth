# AuraWealth

A Streamlit interview demo for a consumer wealth-management experience.

## Foundation milestone

The app contains one mock client, Alex Tan, a client/advisor UI shell, and the On-Demand Insights agent. An OpenAI LLM classifies each user question into one of the supported agent flows before LangGraph runs the specialist. RAG, scenario calculations, and advisor escalations are intentionally added in later milestones.

## Run locally

Create a virtual environment, install dependencies, then run:

```bash
streamlit run app.py
```

The mock data lives in `data/mock_client.json`. It is synthetic and is not financial advice.

Create an ignored `.env.local` with `OPENAI_API_KEY` before using chat. The secure setup flow creates this file locally.

Use **Build semantic index** in the sidebar to embed 1,008 synthetic, approved chunks from 12 AuraWealth guidance documents. Chat citations are filtered to approved client content.
