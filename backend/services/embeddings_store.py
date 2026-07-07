import os

import numpy as np
import pandas as pd
import torch

DEFAULT_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "text_chunks_and_embeddings_df.csv")


def _parse_embedding(raw: str) -> np.ndarray:
    """
    The embeddings were saved via `str(torch.tensor)`, e.g. "tensor([0.1, 0.2, ...])".
    Strip the tensor(...) wrapper and any stray brackets, then parse the floats.
    """
    cleaned = (
        raw.replace("tensor(", "")
        .replace("[", "")
        .replace("]", "")
        .replace(")", "")
    )
    return np.array([float(x) for x in cleaned.split(",") if x.strip() != ""])


def load_embeddings_store(csv_path: str = None):
    """
    Returns (pages_and_chunks, embeddings) where pages_and_chunks is a list of
    dicts (one per chunk) and embeddings is a (N, D) float32 torch tensor.
    """
    csv_path = csv_path or os.getenv("EMBEDDINGS_CSV_PATH", DEFAULT_CSV_PATH)
    csv_path = os.path.abspath(csv_path)

    if not os.path.isfile(csv_path):
        raise FileNotFoundError(
            f"Could not find embeddings CSV at '{csv_path}'. "
            "Set EMBEDDINGS_CSV_PATH or run create_embeddings.py first."
        )

    df = pd.read_csv(csv_path)
    pages_and_chunks = df.to_dict(orient="records")

    cleaned_embeddings = [_parse_embedding(e) for e in df["embedding"]]
    embeddings_matrix = np.vstack(cleaned_embeddings)
    embeddings = torch.tensor(embeddings_matrix, dtype=torch.float32)

    return pages_and_chunks, embeddings
