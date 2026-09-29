from pathlib import Path

from extractors import extract_text
from document import Document, Chunk
from chunker import chunk_text
from embeddings import get_embedding
from search import search_chunks
from context import build_context, build_sources
from generator import generate_answer
from vector_store import save_chunks, load_store


# ============================================================
# CONFIGURATION
# ============================================================

uploads_folder = Path(__file__).resolve().parent / "uploads"
uploads_folder.mkdir(parents=True, exist_ok=True)

documents = []
chunks = []
conversation_history = []


# ============================================================
# CONVERSATION-AWARE SEARCH QUERY
# ============================================================

def build_search_query(query, conversation_history):
    """
    Builds a search query using the current question and
    previous conversation context.

    This allows follow-up questions such as:

        User: What are the advantages of AI?
        User: Which of these is useful in education?
        User: How can students use it?

    to be understood using previous questions and answers.
    """

    if not conversation_history:
        return query

    # Include the previous few turns rather than only one turn.
    # This gives the semantic search more context for follow-up
    # questions while preventing the query from becoming huge.
    recent_history = conversation_history[-3:]

    history_text = []

    for turn in recent_history:
        history_text.append(
            f"""
Previous question:
{turn["question"]}

Previous answer:
{turn["answer"]}
"""
        )

    return f"""
Conversation history:
{"".join(history_text)}

Current question:
{query}
"""


# ============================================================
# LOAD EXISTING VECTOR STORE
# ============================================================

store = load_store(uploads_folder)


# ============================================================
# FIRST RUN - NO VECTOR STORE
# ============================================================

if store is None:

    print("\nNo vector store found.")
    print("Creating embeddings for all uploaded files...")

    files_to_process = [
        file
        for file in uploads_folder.iterdir()
        if file.is_file()
    ]

    chunks = []


# ============================================================
# EXISTING VECTOR STORE
# ============================================================

else:

    saved_files, current_files, saved_chunks = store

    saved_file_names = set(saved_files.keys())
    current_file_names = set(current_files.keys())

    added_files = current_file_names - saved_file_names
    removed_files = saved_file_names - current_file_names

    changed_files = set()

    for filename in saved_file_names & current_file_names:

        if saved_files[filename] != current_files[filename]:
            changed_files.add(filename)


    # --------------------------------------------------------
    # NOTHING CHANGED
    # --------------------------------------------------------

    if not added_files and not removed_files and not changed_files:

        chunks = saved_chunks

        print("\nAll files are unchanged.")
        print("Using saved embeddings.")

        files_to_process = []


    # --------------------------------------------------------
    # FILES CHANGED
    # --------------------------------------------------------

    else:

        print("\nChanges detected in uploads.")

        if added_files:
            print("Added files:", added_files)

        if removed_files:
            print("Removed files:", removed_files)

        if changed_files:
            print("Changed files:", changed_files)


        # Keep chunks belonging only to unchanged files
        chunks = [
            chunk
            for chunk in saved_chunks
            if chunk.filename not in (
                added_files
                | removed_files
                | changed_files
            )
        ]


        # Process only newly added or changed files
        files_to_process = [
            file
            for file in uploads_folder.iterdir()
            if file.is_file()
            and file.name in (
                added_files
                | changed_files
            )
        ]


# ============================================================
# EXTRACT TEXT + CREATE EMBEDDINGS
# ============================================================

for file in files_to_process:

    print(f"\nProcessing: {file.name}")

    try:
        text = extract_text(file)

    except Exception as e:
        print(f"Error extracting {file.name}: {e}")
        continue


    document = Document(
        filename=file.name,
        file_type=file.suffix.lower(),
        text=text
    )


    document_chunks = chunk_text(document.text)


    for i, chunk_text_value in enumerate(
        document_chunks,
        start=1
    ):

        print(
            f"Creating embedding for "
            f"{document.filename} - Chunk {i}"
        )


        try:
            embedding = get_embedding(chunk_text_value)

        except Exception as e:
            print(
                f"Error creating embedding for "
                f"{document.filename} - Chunk {i}: {e}"
            )
            continue


        chunk = Chunk(
            filename=document.filename,
            chunk_id=i,
            text=chunk_text_value,
            embedding=embedding
        )


        chunks.append(chunk)


# ============================================================
# SAVE VECTOR STORE
# ============================================================

if files_to_process or store is None:

    save_chunks(
        chunks,
        uploads_folder
    )

    print("\nVector store saved.")


# ============================================================
# CHAT LOOP
# ============================================================

while True:

    query = input("\nAsk a question: ")


    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    if query.lower().strip() in [
        "exit",
        "quit",
        "q"
    ]:

        print("\nChatbot stopped.")
        break


    # --------------------------------------------------------
    # EMPTY QUESTION
    # --------------------------------------------------------

    if not query.strip():
        continue


    # --------------------------------------------------------
    # BUILD SEARCH QUERY
    # --------------------------------------------------------

    search_query = build_search_query(
        query,
        conversation_history
    )


    print("\n===== SEARCH QUERY =====")
    print(search_query)


    # --------------------------------------------------------
    # SEARCH DOCUMENT CHUNKS
    # --------------------------------------------------------

    results = search_chunks(
        chunks,
        search_query
    )


    print("\n===== SEARCH RESULTS =====")


    # --------------------------------------------------------
    # NO RESULTS
    # --------------------------------------------------------

    if not results:

        print("No relevant chunks found.")

        print("\n===== ANSWER =====")

        print(
            "I couldn't find relevant information in the "
            "uploaded files to answer that question."
        )

        # IMPORTANT:
        # We do NOT add this failed answer to conversation
        # history because it contains no useful document-based
        # information.
        continue


    # --------------------------------------------------------
    # DISPLAY SEARCH RESULTS
    # --------------------------------------------------------

    for chunk, score in results:

        print("\nFile:", chunk.filename)
        print("Chunk ID:", chunk.chunk_id)
        print("Score:", score)
        print(chunk.text)


    # --------------------------------------------------------
    # BUILD CONTEXT
    # --------------------------------------------------------

    context = build_context(results)


    print("\n===== CONTEXT =====")
    print(context)


    # --------------------------------------------------------
    # GENERATE ANSWER
    # --------------------------------------------------------

    answer = generate_answer(
        query,
        context,
        conversation_history
    )


    # --------------------------------------------------------
    # BUILD SOURCES
    # --------------------------------------------------------

    sources = build_sources(results)


    # --------------------------------------------------------
    # DISPLAY ANSWER
    # --------------------------------------------------------

    print("\n===== ANSWER =====")
    print(answer)


    print("\n===== SOURCES =====")
    print(sources)


    # --------------------------------------------------------
    # SAVE CONVERSATION HISTORY
    # --------------------------------------------------------

    conversation_history.append({
        "question": query,
        "answer": answer
    })


    # --------------------------------------------------------
    # DISPLAY HISTORY COUNT
    # --------------------------------------------------------

    print(
        f"\n===== HISTORY =====\n"
        f"Conversation turns: {len(conversation_history)}"
    )