"""
Loads a single shared SentenceTransformer instance so it is only
initialized once per process (both retrieval and embedding creation
import this module instead of instantiating their own copies).
"""
import os

from sentence_transformers import SentenceTransformer

device = os.getenv("EMBEDDING_DEVICE", "cpu")

print(f"[embed_model] Loading embedding model on device: {device}")
embedding_model = SentenceTransformer(model_name_or_path="all-mpnet-base-v2", device=device)
embedding_model.to(device)
print("[embed_model] Embedding model loaded successfully")


def embed_text(pages_and_chunks_over_min_token_len, batch_size: int = 32):
    """Embed a list of chunk dicts in place, adding an 'embedding' key to each."""
    all_chunks = [item["sentence_chunk"] for item in pages_and_chunks_over_min_token_len]

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        embeddings = embedding_model.encode(
            batch,
            device=device,
            convert_to_tensor=True,
            show_progress_bar=False,
        )
        for j, emb in enumerate(embeddings):
            pages_and_chunks_over_min_token_len[i + j]["embedding"] = emb
