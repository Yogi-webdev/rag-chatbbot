import numpy as np
from embeddings import get_embedding


def cosine_similarity(vector1, vector2):

    vector1 = np.array(vector1, dtype=float)
    vector2 = np.array(vector2, dtype=float)

    if vector1.shape != vector2.shape:
        return 0.0

    norm_product = np.linalg.norm(vector1) * np.linalg.norm(vector2)
    if norm_product == 0:
        return 0.0

    similarity = np.dot(vector1, vector2) / norm_product

    return similarity


def search_chunks(chunks, query):
    """Return ranked results from the supplied chunks.

    The caller has already filtered these chunks to the active files, so using
    them directly prevents results from deselected files leaking into a search.
    Threshold selection belongs to the UI, not this low-level function.
    """
    try:
        query_embedding = get_embedding(query)
    except Exception as error:
        print(f"Error creating query embedding: {error}")
        return []

    if query_embedding is None:
        return []

    results = []

    for chunk in chunks or []:
        if chunk.embedding is None:
            continue

        if len(chunk.embedding) != len(query_embedding):
            continue

        score = cosine_similarity(query_embedding, chunk.embedding)
        results.append((chunk, score))

    results.sort(key=lambda item: item[1], reverse=True)

    return results[:10]
