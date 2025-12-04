"""
Local test script for RAG engine.
Tests retrieval and generation capabilities in isolation.
"""

import os
from dotenv import load_dotenv
from rag import RAGEngine


def main():
    print("=" * 60)
    print("RAG Engine Local Test")
    print("=" * 60)

    # 1. Load and verify environment
    print("\n[1] Loading environment variables...")
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("✗ ERROR: GOOGLE_API_KEY not found in .env file!")
        return
    print("✓ GOOGLE_API_KEY loaded successfully")

    # 2. Hardcoded Test Features
    # Using GOLDEN SUBSET for filtering:
    # - Strict Identity: category, area, price_level (always used)
    # - Vibe/Operation: is_open_24_7, outdoor_seating, live_music (only if True)
    test_features = {
        # === GOLDEN SUBSET - STRICT IDENTITY (Always Filter) ===
        "category": "Fast Food Restaurant",
        "area": "DHA",
        "price_level": "PRICE_LEVEL_MODERATE",
        # === GOLDEN SUBSET - VIBE/OPERATION (Filter only if True) ===
        "is_open_24_7": False,
        "outdoor_seating": False,
        "live_music": False,
        # === OTHER FEATURES (Sent but NOT used for filtering) ===
        # These are still sent to maintain API compatibility
        # but are ignored in the retrieval process
        "dine_in": True,
        "takeout": True,
        "serves_lunch": True,
        "serves_dinner": True,
        "good_for_groups": True,
        "delivery": False,
        "reservable": False,
        "serves_breakfast": False,
        "serves_coffee": False,
        "serves_dessert": False,
        "good_for_children": False,
        "good_for_watching_sports": False,
        "restroom": False,
        "parking_free_lot": False,
        "parking_free_street": False,
        "accepts_debit_cards": False,
        "accepts_cash_only": False,
        "wheelchair_accessible": False,
        "open_after_midnight": False,
        "is_closed_any_day": False,
    }

    print(f"\n[2] Test Features:")
    for key, value in test_features.items():
        print(f"   - {key}: {value}")

    try:
        # 3. Initialize RAG Engine
        print("\n[3] Initializing RAG Engine...")
        rag_engine = RAGEngine()
        print("✓ RAG Engine initialized successfully")

        # 4. Step 1: Test Retrieval
        print("\n" + "=" * 60)
        print("STEP 1: RETRIEVAL TEST")
        print("=" * 60)

        reviews = rag_engine.retrieve_reviews(test_features, k=5)

        if reviews:
            print(f"\n✓ Retrieved {len(reviews)} reviews:\n")
            for i, review in enumerate(reviews, 1):
                print(f"--- Review {i} ---")
                print(review)
                print()
        else:
            print("⚠ No reviews retrieved!")

        # 5. Step 2: Test Generation
        print("=" * 60)
        print("STEP 2: GENERATION TEST")
        print("=" * 60)

        advice = rag_engine.generate_advice(test_features)

        print("\n✓ Generated Advice:\n")
        print(advice)
        print()

        print("=" * 60)
        print("Test completed successfully!")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n✗ ERROR: File or directory not found - {e}")
        print("Make sure chroma_db_data exists and is populated.")

    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
