"""
Data Ingestion Script for ChromaDB Vector Store
Ingests restaurant reviews with metadata into a local ChromaDB instance.
"""

import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def load_and_merge_data():
    """Load CSV files and perform left join on reviews."""
    print("Loading data files...")

    # Load datasets
    restaurants_df = pd.read_csv("RAG-data/Restaurants.csv")
    reviews_df = pd.read_csv("RAG-data/Reviews.csv")

    print(f"Loaded {len(restaurants_df)} restaurants")
    print(f"Loaded {len(reviews_df)} reviews")

    # Perform LEFT JOIN on reviews
    merged_df = reviews_df.merge(
        restaurants_df,
        on="google_maps_link",
        how="left",
        suffixes=("_review", "_restaurant")
    )

    print(f"Merged dataset: {len(merged_df)} records")

    return merged_df


def clean_data(df):
    """Clean the merged dataframe."""
    print("\nCleaning data...")

    # Drop rows where review_text is empty
    initial_count = len(df)
    df = df.dropna(subset=["text"])
    df = df[df["text"].str.strip() != ""]
    print(f"Dropped {initial_count - len(df)} rows with empty review_text")

    # Define all boolean columns
    boolean_columns = [
        "dine_in", "takeout", "delivery", "reservable",
        "serves_breakfast", "serves_lunch", "serves_dinner",
        "serves_coffee", "serves_dessert", "outdoor_seating",
        "live_music", "good_for_children", "good_for_groups",
        "good_for_watching_sports", "restroom", "parking_free_lot",
        "parking_free_street", "accepts_debit_cards", "accepts_cash_only",
        "wheelchair_accessible", "is_open_24_7", "open_after_midnight",
        "is_closed_any_day"
    ]

    # Fill NaN values in boolean columns with False
    for col in boolean_columns:
        if col in df.columns:
            df[col] = df[col].fillna(False)
            # Convert to boolean type
            df[col] = df[col].astype(bool)

    print(f"Cleaned dataset: {len(df)} records ready for ingestion")

    return df.reset_index(drop=True)


def initialize_chromadb():
    """Initialize ChromaDB persistent client and collection."""
    print("\nInitializing ChromaDB...")

    # Create persistent client
    client = chromadb.PersistentClient(path="./chroma_db_data")

    # Get or create collection
    collection = client.get_or_create_collection(
        name="restaurant_reviews",
        metadata={"description": "Restaurant reviews with metadata"}
    )

    print(f"Collection 'restaurant_reviews' initialized")
    print(f"Current collection count: {collection.count()}")

    return collection


def prepare_metadata(row):
    """Prepare metadata dictionary from a dataframe row."""
    # Define metadata columns
    categorical_columns = ["area", "price_level", "category"]
    boolean_columns = [
        "dine_in", "takeout", "delivery", "reservable",
        "serves_breakfast", "serves_lunch", "serves_dinner",
        "serves_coffee", "serves_dessert", "outdoor_seating",
        "live_music", "good_for_children", "good_for_groups",
        "good_for_watching_sports", "restroom", "parking_free_lot",
        "parking_free_street", "accepts_debit_cards", "accepts_cash_only",
        "wheelchair_accessible", "is_open_24_7", "open_after_midnight",
        "is_closed_any_day"
    ]

    metadata = {}

    # Add categorical columns
    for col in categorical_columns:
        if col in row and pd.notna(row[col]):
            metadata[col] = str(row[col])

    # Add boolean columns (keep as native bool)
    for col in boolean_columns:
        if col in row:
            metadata[col] = bool(row[col])

    return metadata


def ingest_data(collection, df, batch_size=100):
    """Ingest data into ChromaDB with progress logging."""
    print(f"\nIngesting {len(df)} records into ChromaDB...")
    print("=" * 60)

    # Process in batches with progress bar
    for i in tqdm(range(0, len(df), batch_size), desc="Ingesting batches"):
        batch_df = df.iloc[i:i + batch_size]

        # Prepare batch data
        documents = []
        ids = []
        metadatas = []

        for idx, row in batch_df.iterrows():
            # Document: review_text
            documents.append(str(row["text"]))

            # ID: unique string
            ids.append(f"review_{idx}")

            # Metadata: dictionary with specified columns
            metadata = prepare_metadata(row)
            metadatas.append(metadata)

        # Add batch to collection
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )

    print("=" * 60)
    print(f"\n✓ Successfully ingested {len(df)} records")
    print(f"✓ Final collection count: {collection.count()}")


def main():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("CHROMADB DATA INGESTION PIPELINE")
    print("=" * 60)

    # Step 1: Load and merge data
    merged_df = load_and_merge_data()

    # Step 2: Clean data
    cleaned_df = clean_data(merged_df)

    # Step 3: Initialize ChromaDB
    collection = initialize_chromadb()

    # Step 4: Ingest data
    ingest_data(collection, cleaned_df)

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
