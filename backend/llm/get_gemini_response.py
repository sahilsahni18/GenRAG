import os

from google import genai

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set. "
                "Add it to your .env file (local) or your host's environment variables (Render)."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def get_gemini_response(context: str, query: str) -> str:
    client = _get_client()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    response = client.models.generate_content(
        model=model,
        contents=f"""
Using the context given below, answer the query. If the context does not
contain the answer, say so instead of making something up.

CONTEXT: {context}

QUERY: {query}
""",
    )

    return response.text
