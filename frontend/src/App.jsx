import React, { useEffect, useRef, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const EXAMPLE_PROMPTS = [
  "What is the difference between an investor and a speculator?",
  "How does Graham define 'margin of safety'?",
  "What should a defensive investor do in a market downturn?",
];

function ScoreBar({ score }) {
  const pct = Math.max(0, Math.min(100, Math.round(score * 100)));
  return (
    <div className="score-bar" aria-hidden="true">
      <div className="score-bar-fill" style={{ width: `${pct}%` }} />
    </div>
  );
}

function SourceEntry({ source, index }) {
  return (
    <li className="ledger-entry">
      <span className="ledger-index">{String(index + 1).padStart(2, "0")}</span>
      <span className="ledger-excerpt">"{source.sentence_chunk}"</span>
      <span className="ledger-leader" aria-hidden="true" />
      <span className="ledger-meta">
        <span className="ledger-page">p.{source.page_number}</span>
        <span className="ledger-score">{source.score.toFixed(3)}</span>
      </span>
      <ScoreBar score={source.score} />
    </li>
  );
}

function Turn({ turn }) {
  return (
    <article className="turn">
      <div className="turn-question">
        <span className="turn-label">Query</span>
        <p>{turn.query}</p>
      </div>

      {turn.status === "loading" && (
        <div className="turn-answer loading">
          <span className="turn-label">Reading</span>
          <p className="skeleton-line" />
          <p className="skeleton-line short" />
        </div>
      )}

      {turn.status === "error" && (
        <div className="turn-answer error">
          <span className="turn-label">Couldn't finish</span>
          <p>{turn.error}</p>
        </div>
      )}

      {turn.status === "done" && (
        <>
          <div className="turn-answer">
            <span className="turn-label">Answer</span>
            <p>{turn.answer}</p>
          </div>

          {turn.sources?.length > 0 && (
            <div className="ledger">
              <span className="turn-label">Referenced passages</span>
              <ul>
                {turn.sources.map((s, i) => (
                  <SourceEntry source={s} index={i} key={i} />
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </article>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [turns, setTurns] = useState([]);
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState("checking");
  const scrollRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/health`)
      .then((r) => r.json())
      .then((d) => {
        if (!cancelled) setHealth(d.status === "ok" ? "ready" : "warming");
      })
      .catch(() => {
        if (!cancelled) setHealth("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [turns]);

  async function submitQuery(q) {
    const question = (q ?? query).trim();
    if (!question || busy) return;

    setQuery("");
    setBusy(true);
    const turnId = Date.now();
    setTurns((prev) => [...prev, { id: turnId, query: question, status: "loading" }]);

    try {
      const res = await fetch(`${API_URL}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, top_k: 3 }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "The server couldn't answer that one.");
      }

      setTurns((prev) =>
        prev.map((t) =>
          t.id === turnId ? { ...t, status: "done", answer: data.answer, sources: data.sources } : t
        )
      );
    } catch (err) {
      setTurns((prev) =>
        prev.map((t) => (t.id === turnId ? { ...t, status: "error", error: err.message } : t))
      );
    } finally {
      setBusy(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    submitQuery();
  }

  return (
    <div className="app">
      <aside className="spine">
        <div className="spine-inner">
          <div className="brand">
            <span className="brand-mark">GR</span>
            <div>
              <h1>GenRAG</h1>
              <p className="brand-sub">an index, not a summary</p>
            </div>
          </div>

          <p className="spine-copy">
            Every answer here is pulled from actual passages of{" "}
            <em>The Intelligent Investor</em> — retrieved by similarity, then
            handed to Gemini to explain in context.
          </p>

          <form className="ask-form" onSubmit={handleSubmit}>
            <label htmlFor="query">Ask the book something</label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submitQuery();
                }
              }}
              placeholder="e.g. What does Graham say about Mr. Market?"
              rows={4}
            />
            <button type="submit" disabled={busy || !query.trim()}>
              {busy ? "Reading…" : "Ask"}
            </button>
          </form>

          <div className="examples">
            <span className="turn-label">Try one</span>
            <ul>
              {EXAMPLE_PROMPTS.map((p) => (
                <li key={p}>
                  <button type="button" onClick={() => submitQuery(p)} disabled={busy}>
                    {p}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className={`status status-${health}`}>
            <span className="status-dot" />
            {health === "ready" && "Backend ready"}
            {health === "warming" && "Backend waking up"}
            {health === "checking" && "Checking backend…"}
            {health === "offline" && "Backend unreachable"}
          </div>
        </div>
      </aside>

      <main className="pages" ref={scrollRef}>
        {turns.length === 0 ? (
          <div className="empty-state">
            <h2>Open to any page.</h2>
            <p>
              Ask a question in the panel on the left. GenRAG will surface the
              exact excerpts it used, with their retrieval score, so you can
              check the source yourself.
            </p>
          </div>
        ) : (
          turns.map((t) => <Turn turn={t} key={t.id} />)
        )}
      </main>
    </div>
  );
}
