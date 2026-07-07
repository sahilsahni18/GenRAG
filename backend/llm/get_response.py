from llm.get_gemini_response import get_gemini_response
from services.retrieve import retrieve_relevant_resources


def ask(query, embeddings, pages_and_chunks, embeddings_df_save_path=None, top_k: int = 3):
    """
    Takes a query, retrieves the most relevant chunks, and asks Gemini to
    answer using them as context.
    """
    scores, indices = retrieve_relevant_resources(
        query=query, embeddings=embeddings, n_resources_to_return=top_k
    )

    context_items = [pages_and_chunks[i] for i in indices]
    context = "- " + "\n- ".join([item["sentence_chunk"] for item in context_items])

    for i, item in enumerate(context_items):
        item["score"] = float(scores[i])

    ans = get_gemini_response(query=query, context=context)

    return ans
