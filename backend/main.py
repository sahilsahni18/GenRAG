import os
from contextlib import asynccontextmanager
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

from services.embeddings_store import load_embeddings_store  # noqa: E402
from services.retrieve import retrieve_relevant_resources  # noqa: E402
from llm.get_gemini_response import get_gemini_response  # noqa: E402

STATE = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] Loading embeddings store...")
    try:
        pages_and_chunks, embeddings = load_embeddings_store()
        STATE["pages_and_chunks"] = pages_and_chunks
        STATE["embeddings"] = embeddings
        print(f"[startup] Loaded {len(pages_and_chunks)} chunks.")
    except Exception as exc:
        # Don't crash the whole server if the CSV is missing; surface a clear
        # 503 from /api/query instead so the deploy can still boot & be debugged.
        print(f"[startup] Failed to load embeddings store: {exc}")
    yield
    STATE.clear()


app = FastAPI(title="GenRAG API", version="1.0.0", lifespan=lifespan)

_origins_env = os.getenv("FRONTEND_ORIGIN", "*")
_allow_origins = ["*"] if _origins_env.strip() == "*" else [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The question to ask about the document.")
    top_k: int = Field(3, ge=1, le=10, description="Number of source chunks to retrieve.")


class Source(BaseModel):
    page_number: int
    sentence_chunk: str
    score: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Source]


@app.get("/")
def root():
    return {"service": "GenRAG API", "status": "running", "docs": "/docs"}


@app.get("/api/health")
def health():
    loaded = "embeddings" in STATE
    return {
        "status": "ok" if loaded else "not_ready",
        "chunks_loaded": len(STATE.get("pages_and_chunks", [])),
    }


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if "embeddings" not in STATE:
        raise HTTPException(
            status_code=503,
            detail="Embeddings store is not loaded. Check server logs / EMBEDDINGS_CSV_PATH.",
        )

    pages_and_chunks = STATE["pages_and_chunks"]
    embeddings = STATE["embeddings"]

    scores, indices = retrieve_relevant_resources(
        query=req.query, embeddings=embeddings, n_resources_to_return=req.top_k
    )

    sources: List[Source] = []
    context_parts = []
    for score, idx in zip(scores, indices):
        item = pages_and_chunks[int(idx)]
        sources.append(
            Source(
                page_number=int(item["page_number"]),
                sentence_chunk=item["sentence_chunk"],
                score=float(score),
            )
        )
        context_parts.append(item["sentence_chunk"])

    context = "- " + "\n- ".join(context_parts)

    try:
        answer = get_gemini_response(context=context, query=req.query)
    except RuntimeError as exc:
        # e.g. missing GEMINI_API_KEY
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}")

    return QueryResponse(query=req.query, answer=answer, sources=sources)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
