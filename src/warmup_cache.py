"""
Warmup script to cache ChromaDB embedding model.
Performs a dummy query to trigger model download during initialization.
"""

import os
import chromadb


def warmup_chroma_cache():
    """Perform a dummy query to cache the embedding model."""
    print("\nWarming up ChromaDB cache...")

    # Get DB path from environment variable
    db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db_data")

    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection("restaurant_reviews")

        # Perform a simple query to trigger model download
        collection.query(query_texts=["test restaurant"], n_results=1)

        print("✓ ChromaDB cache warmed up successfully!")
        print("  Embedding model cached for fast inference")

    except Exception as e:
        print(f"⚠️ Warning: Cache warmup failed: {e}")
        print("  Model will be downloaded on first API request")


if __name__ == "__main__":
    warmup_chroma_cache()
