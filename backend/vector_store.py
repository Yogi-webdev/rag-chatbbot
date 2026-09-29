from pathlib import Path

import chromadb

from document import Chunk, Document


BACKEND_DIR = Path(__file__).resolve().parent
VECTOR_STORE_FILE = BACKEND_DIR / "vector_store.json"
CHROMA_PATH = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "file_chatbot_chunks"


def get_file_metadata(uploads_folder):
    metadata = {}
    for file in uploads_folder.iterdir():
        if file.is_file():
            metadata[file.name] = {
                "size": file.stat().st_size,
                "modified": file.stat().st_mtime
            }
    return metadata


def _get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def reset_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def ensure_collection_dimension(expected_dim):
    collection = _get_collection()
    try:
        sample = collection.get(limit=1, include=["embeddings"])
        if sample.get("embeddings") and sample["embeddings"][0] is not None:
            if len(sample["embeddings"][0]) != expected_dim:
                return reset_collection()
    except Exception:
        return reset_collection()
    return collection


def save_chunks(chunks, uploads_folder):
    collection = _get_collection()
    valid_chunks = [c for c in chunks if c.embedding is not None]
    print(f"DEBUG save_chunks: Starting to save {len(valid_chunks)} valid chunks (total input: {len(chunks)})")
    
    # A re-upload can contain fewer chunks than the previous version. Remove
    # the old chunks for each replaced file so stale text cannot be retrieved.
    for filename in {chunk.filename for chunk in valid_chunks}:
        try:
            collection.delete(where={"filename": filename})
        except Exception:
            pass

    saved_count = 0
    for chunk in valid_chunks:
        chunk_id = f"{chunk.filename}:{chunk.chunk_id}"
        try:
            collection.upsert(
                ids=[chunk_id],
                embeddings=[chunk.embedding],
                metadatas=[{
                    "filename": chunk.filename,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text
                }],
                documents=[chunk.text]
            )
            saved_count += 1
        except Exception as e:
            print(f"Error upserting chunk {chunk_id}: {e}")
            continue

    print(f"DEBUG save_chunks: Successfully saved {saved_count}/{len(valid_chunks)} chunks to ChromaDB")
    print(f"DEBUG save_chunks: Collection now contains {collection.count()} total chunks")


def delete_file_from_store(filename, uploads_folder=None):
    try:
        collection = _get_collection()
        collection.delete(where={"filename": filename})
        print(f"Deleted chunks for {filename} from ChromaDB")
    except Exception as e:
        print(f"Error deleting {filename} from ChromaDB: {e}")

    for folder in [uploads_folder, BACKEND_DIR / "uploads", BACKEND_DIR.parent / "uploads"]:
        if folder:
            file_path = Path(folder) / filename
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"Deleted physical file: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

    return True


def load_store(uploads_folder):
    try:
        collection = _get_collection()
        total_count = collection.count()

        if total_count == 0:
            return None

        saved_files = get_file_metadata(uploads_folder)
        current_files = get_file_metadata(uploads_folder)

        results = collection.get(limit=total_count, include=["metadatas", "documents", "embeddings"])
        chunks = []

        docs = results.get("documents")
        if docs is None:
            docs = []
        embs = results.get("embeddings")
        if embs is None:
            embs = []
        metas = results.get("metadatas")
        if metas is None:
            metas = []

        for idx, metadata in enumerate(metas):
            if not metadata:
                continue

            chunk_text_content = docs[idx] if idx < len(docs) else metadata.get("text", "")
            chunk_embedding = embs[idx] if idx < len(embs) else None

            chunk = Chunk(
                filename=metadata.get("filename"),
                chunk_id=metadata.get("chunk_id"),
                text=chunk_text_content,
                embedding=chunk_embedding
            )
            chunks.append(chunk)

        return saved_files, current_files, chunks
    except Exception as e:
        print(f"Error loading store: {e}")
        return None
