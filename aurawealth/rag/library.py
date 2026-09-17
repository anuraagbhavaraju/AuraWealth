import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env.local")
INDEX_PATH = ROOT / "data" / "chroma"
COLLECTION = "aurawealth_approved_guidance"
CHUNKS_PER_DOCUMENT = 84

DOCUMENTS = [
    ("Managing Recurring Expenses", "spending", "Review recurring services regularly. Compare each charge with how often you use it and cancel services that no longer support your priorities."),
    ("Subscription Review Checklist", "spending", "Group recurring charges by service, compare periods, and investigate increases before changing a budget."),
    ("Household Cash Flow Basics", "cash_flow", "A monthly plan helps connect income, fixed commitments, living costs, and financial goals."),
    ("Emergency Fund Guide", "goals", "Keep accessible cash for unexpected costs and set a target that reflects essential expenses."),
    ("Planning for Short-Term Goals", "goals", "Separate goal savings from essential reserves and use a clear target date."),
    ("Mortgage Prepayment Overview", "mortgage", "Extra mortgage payments can reduce outstanding principal and may reduce future interest."),
    ("Mortgage Decision Questions", "mortgage", "Check loan terms, cash reserves, and other commitments before deciding on a prepayment."),
    ("Understanding Investment Risk", "investing", "Investment values can change. Risk discussions should consider a client’s objectives and time horizon."),
    ("Portfolio Diversification Primer", "investing", "Diversification spreads exposure across investments and does not guarantee against loss."),
    ("Client Communication Standard", "service", "Use clear language, identify assumptions, and invite a client to speak with an advisor for personal advice."),
    ("Digital Security for Clients", "security", "Never request passwords or transfer instructions through ordinary chat messages."),
    ("Advisor Escalation Policy", "governance", "Requests for personalised recommendations or transactions require human advisor review."),
]


def _client():
    return chromadb.PersistentClient(path=str(INDEX_PATH))


def _collection():
    return _client().get_or_create_collection(COLLECTION, metadata={"description": "Synthetic approved demo guidance"})


def _embedding(inputs: list[str]) -> list[list[float]]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("The OpenAI API key is not configured.")
    response = OpenAI().embeddings.create(model="text-embedding-3-small", input=inputs)
    return [item.embedding for item in response.data]


def chunk_count() -> int:
    return _collection().count()


def build_index() -> int:
    collection = _collection()
    if collection.count() >= len(DOCUMENTS) * CHUNKS_PER_DOCUMENT:
        return collection.count()

    ids, texts, metadata = [], [], []
    for document_number, (title, topic, guidance) in enumerate(DOCUMENTS, start=1):
        for section in range(1, CHUNKS_PER_DOCUMENT + 1):
            ids.append(f"doc-{document_number}-section-{section}")
            texts.append(f"{title}. Section {section}: {guidance} This is approved client education for AuraWealth.")
            metadata.append({"title": title, "topic": topic, "audience": "client", "approved": "true", "language": "en", "section": section})

    for start in range(0, len(ids), 100):
        end = start + 100
        collection.add(ids=ids[start:end], documents=texts[start:end], metadatas=metadata[start:end], embeddings=_embedding(texts[start:end]))
    return collection.count()


def retrieve(query: str, limit: int = 3) -> list[dict]:
    collection = _collection()
    if collection.count() == 0:
        return []
    result = collection.query(
        query_embeddings=_embedding([query]),
        n_results=collection.count(),
        where={"$and": [{"audience": "client"}, {"approved": "true"}]},
    )
    sources = []
    seen_titles = set()
    for meta in result["metadatas"][0]:
        if meta["title"] not in seen_titles:
            sources.append({"title": meta["title"], "topic": meta["topic"], "section": meta["section"]})
            seen_titles.add(meta["title"])
        if len(sources) == limit:
            break
    return sources
