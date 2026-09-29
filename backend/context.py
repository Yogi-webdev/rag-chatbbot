def build_context(results):

    if not results:
        return ""

    context_parts = []

    for chunk, score in results:

        context_parts.append(
            f"""Source: {chunk.filename}
Chunk: {chunk.chunk_id}
Similarity Score: {score:.4f}
Content:
{chunk.text}
"""
        )

    return "\n".join(context_parts)


def build_sources(results):

    if not results:
        return ""

    sources = []

    for chunk, score in results:

        source = f"- {chunk.filename} (Chunk {chunk.chunk_id})"

        if source not in sources:
            sources.append(source)

    return "\n".join(sources)