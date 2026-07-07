# Deploying GenRAG

The project is split into two deployable pieces:

- **`backend/`** — a FastAPI wrapper around the existing retrieval + Gemini
  pipeline. Deploys to **Render** as a web service.
- **`frontend/`** — a small React (Vite) chat UI that calls the backend.
  Deploys to **Vercel**.

The original CLI scripts (`main.py`, `create_embeddings.py` at the repo root)
are unchanged and still work locally if you just want the terminal tool.

---

## 1. Get a Gemini API key

Create one at https://aistudio.google.com/apikey. You'll need it as
`GEMINI_API_KEY` in the backend.

---

## 2. Deploy the backend to Render

**Option A — Blueprint (recommended)**

1. Push this repo to GitHub.
2. In Render, click **New > Blueprint** and pick the repo. Render will read
   `render.yaml` at the repo root and configure the service automatically
   (root dir `backend`, build command, start command, health check).
3. When prompted, set the `GEMINI_API_KEY` env var (marked `sync: false`, so
   Render asks for it instead of committing it).
4. After the first deploy, copy the service URL, e.g.
   `https://genrag-backend.onrender.com`.
5. Once you have your Vercel URL (step 3), come back and set the backend's
   `FRONTEND_ORIGIN` env var to it (comma-separate if you have more than
   one), then redeploy so CORS only allows your frontend.

**Option B — Manual web service**

1. In Render, **New > Web Service**, connect the repo.
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add env vars: `GEMINI_API_KEY`, `GEMINI_MODEL` (optional, defaults to
   `gemini-2.5-flash`), `FRONTEND_ORIGIN`.

**Notes**

- The embeddings CSV (`backend/data/text_chunks_and_embeddings_df.csv`) is
  loaded into memory once at startup — no vector database needed.
- First request after a cold start (Render's free tier sleeps idle services)
  will be slow while the sentence-transformers model downloads/loads.
- Verify it's up: `GET https://<your-backend>.onrender.com/api/health`

---

## 3. Deploy the frontend to Vercel

1. In Vercel, **Add New > Project**, import the same repo.
2. Set **Root Directory** to `frontend`.
3. Framework preset: Vite (auto-detected). Build command `npm run build`,
   output directory `dist` (Vercel fills these in automatically).
4. Add an environment variable:
   - `VITE_API_URL` = the Render backend URL from step 2, e.g.
     `https://genrag-backend.onrender.com` (no trailing slash).
5. Deploy. Then go back to Render and set `FRONTEND_ORIGIN` to the Vercel URL
   Vercel gives you (e.g. `https://genrag.vercel.app`) so CORS is locked down.

---

## 4. Local development

Backend:

```sh
cd backend
python3 -m venv env && source env/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in GEMINI_API_KEY
uvicorn main:app --reload
```

Frontend:

```sh
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev
```

---

## 5. Regenerating embeddings for a different PDF

The CSV under `backend/data/` was produced by the root-level
`create_embeddings.py` script (uses the full `requirements.txt`, not the
slim backend one — it needs spaCy, PyMuPDF, etc). To index a new document:

```sh
python3 -m venv env && source env/bin/activate
pip install -r requirements.txt
python3 create_embeddings.py   # prompts for a PDF path under data/
```

Then copy the resulting `data/text_chunks_and_embeddings_df.csv` into
`backend/data/` and redeploy the backend.
