import textwrap
from timeit import default_timer as timer

import torch
from sentence_transformers import util

from services.embed_model import embedding_model


def print_wrapped(text, wrap_length=80):
    wrapped_text = textwrap.fill(text, wrap_length)
    print(wrapped_text)


def retrieve_relevant_resources(
    query: str,
    embeddings: torch.Tensor,
    model=embedding_model,
    n_resources_to_return: int = 3,
    print_time: bool = False,
):
    """
    Embeds a query with `model` and returns the top-k scores and indices
    against the pre-computed `embeddings` matrix.
    """
    query_embedding = model.encode(query, convert_to_tensor=True)

    start_time = timer()
    dot_scores = util.dot_score(query_embedding, embeddings)[0]
    end_time = timer()

    if print_time:
        print(f"[INFO] Time taken to get scores on {len(embeddings)} embeddings: {end_time - start_time:.5f} seconds.")

    k = min(n_resources_to_return, len(embeddings))
    scores, indices = torch.topk(input=dot_scores, k=k)

    return scores, indices


def print_top_results_and_scores(
    query: str,
    embeddings: torch.Tensor,
    pages_and_chunks: list,
    n_resources_to_return: int = 3,
):
    scores, indices = retrieve_relevant_resources(
        query=query, embeddings=embeddings, n_resources_to_return=n_resources_to_return
    )

    print(f"Query: {query}\n")
    print("Results:")
    for score, index in zip(scores, indices):
        print(f"Score: {score:.4f}")
        print_wrapped(pages_and_chunks[index]["sentence_chunk"])
        print("\n")
