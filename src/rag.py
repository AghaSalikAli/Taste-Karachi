import os
import chromadb
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from prometheus_client import Counter, Histogram

# --- PROMETHEUS METRICS ---
# Track latency of the RAG pipeline
RAG_LATENCY = Histogram('rag_request_latency_seconds', 'RAG Pipeline Latency')
# Track token usage for cost monitoring
LLM_TOKEN_USAGE = Counter('llm_token_usage_total', 'Total LLM Tokens', ['type'])


class RAGEngine:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # 1. Connect to Vector DB
        # Uses env var CHROMA_DB_PATH if set (Docker), otherwise defaults to local folder
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db_data")
        print(f"Loading Vector DB from: {db_path}...")

        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection("restaurant_reviews")

        # 2. Connect to Gemini (LLM)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("CRITICAL WARNING: GOOGLE_API_KEY is missing! RAG will fail.")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.3
        )

    def retrieve_reviews(self, features, k=5):
        """
        Retrieves relevant reviews based on restaurant features.
        Implements Iterative Query Relaxation with 3 levels of strictness:

        Level 1 (Strict): category + area + price_level + vibe features (if True)
        Level 2 (Relaxed): category + area + price_level only
        Level 3 (Broad): category only

        Returns empty list if no results found at any level.
        """
        category = features.get('category', 'restaurant')
        area = features.get('area', 'Karachi')
        price_level = features.get('price_level', 'moderate')

        # Identify vibe features that are True
        vibe_operation_fields = ["is_open_24_7", "outdoor_seating", "live_music"]
        active_vibe_features = {field: True for field in vibe_operation_fields
                               if features.get(field) is True}

        # ATTEMPT 1: STRICT - All filters including vibe features
        print(f"[Retrieval] Attempt 1 (Strict): category + area + price + vibes")
        results = self._query_with_filters(
            category=category,
            area=area,
            price_level=price_level,
            vibe_features=active_vibe_features,
            k=k
        )

        if results:
            print(f"[Retrieval] ✓ Strict query returned {len(results)} reviews")
            return results

        # ATTEMPT 2: RELAXED - Drop vibe features, keep identity filters
        print(f"[Retrieval] Attempt 2 (Relaxed): category + area + price only")
        results = self._query_with_filters(
            category=category,
            area=area,
            price_level=price_level,
            vibe_features=None,
            k=k
        )

        if results:
            print(f"[Retrieval] ✓ Relaxed query returned {len(results)} reviews")
            return results

        # ATTEMPT 3: BROAD - Category only
        print(f"[Retrieval] Attempt 3 (Broad): category only")
        results = self._query_with_filters(
            category=category,
            area=None,
            price_level=None,
            vibe_features=None,
            k=k
        )

        if results:
            print(f"[Retrieval] ✓ Broad query returned {len(results)} reviews")
            return results

        # FINAL FALLBACK: No results at any level
        print(f"[Retrieval] ✗ No reviews found at any filtering level")
        return []

    def _query_with_filters(self, category, area, price_level, vibe_features, k):
        """
        Helper method to execute a query with specified filters.

        Args:
            category: Restaurant category (required if not None)
            area: Restaurant area (optional)
            price_level: Price level (optional)
            vibe_features: Dict of vibe features {field: True} (optional)
            k: Number of results to return

        Returns:
            List of review documents
        """
        # Construct search query
        query_parts = []
        if category:
            query_parts.append(f"{category}")
        if area:
            query_parts.append(f"in {area}")
        if price_level:
            query_parts.append(f"that is {price_level} price")

        query_text = "Reviews for a " + " ".join(query_parts) + "."

        # Build metadata filter conditions
        conditions = []

        # Add category filter
        if category:
            conditions.append({"category": {"$eq": category}})

        # Add area filter
        if area:
            conditions.append({"area": {"$eq": area}})

        # Add price_level filter
        if price_level:
            conditions.append({"price_level": {"$eq": price_level}})

        # Add vibe feature filters
        if vibe_features:
            for field, value in vibe_features.items():
                conditions.append({field: {"$eq": value}})

        # Construct where filter
        where_filter = None
        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=k,
                where=where_filter
            )
            # Flatten list of lists and return
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"[Retrieval Error] {e}")
            return []

    def generate_advice(self, features):
        start_time = time.time()
        try:
            # A. Retrieve
            reviews = self.retrieve_reviews(features)

            # If no reviews found after all fallback attempts, return early
            if not reviews:
                print("[RAG] No reviews found - skipping LLM request")
                return "No relevant historical reviews found to base advice on."

            reviews_text = "\n- ".join(reviews)

            # Build feature description for prompt (using golden subset)
            feature_desc = f"{features.get('category', 'restaurant')} in {features.get('area', 'Karachi')}"

            # Add vibe/operation features to description if present
            vibe_features = []
            if features.get('outdoor_seating'): vibe_features.append('outdoor seating')
            if features.get('live_music'): vibe_features.append('live music')
            if features.get('is_open_24_7'): vibe_features.append('24/7 operation')

            if vibe_features:
                feature_desc += f" with {', '.join(vibe_features)}"

            # B. Generate
            prompt = (
                f"You are an expert Restaurant Consultant. \n"
                f"A client is opening a new {feature_desc}.\n"
                f"Here are reviews from similar existing restaurants with matching features:\n"
                f"---\n{reviews_text}\n---\n"
                f"Based ONLY on these reviews, list 3 key success factors and 1 potential pitfall "
                f"for the new owner. Be concise."
            )

            response = self.llm.invoke([HumanMessage(content=prompt)])

            # C. Log Metrics
            # Approx 4 chars per token
            input_tokens = len(prompt) / 4
            output_tokens = len(response.content) / 4
            LLM_TOKEN_USAGE.labels(type='input').inc(input_tokens)
            LLM_TOKEN_USAGE.labels(type='output').inc(output_tokens)

            return response.content

        except Exception as e:
            return f"Error generating advice: {str(e)}"

        finally:
            RAG_LATENCY.observe(time.time() - start_time)
