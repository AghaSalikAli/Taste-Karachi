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
        Uses GOLDEN SUBSET of metadata fields to prevent over-filtering.

        Golden Subset:
        - Strict Identity: category, area, price_level (always filter)
        - Vibe/Operation: is_open_24_7, outdoor_seating, live_music (filter only if True)
        """
        # Construct search query from categorical fields
        query_text = (
            f"Reviews for a {features.get('category', 'restaurant')} "
            f"in {features.get('area', 'Karachi')} "
            f"that is {features.get('price_level', 'moderate')} price."
        )

        # Build metadata filter using only GOLDEN SUBSET
        conditions = []

        # 1. STRICT IDENTITY FILTERS (Always Filter)
        strict_identity_fields = ["category", "area", "price_level"]
        for field in strict_identity_fields:
            if features.get(field):
                conditions.append({field: {"$eq": features.get(field)}})

        # 2. VIBE/OPERATION FILTERS (Only Filter if True)
        vibe_operation_fields = ["is_open_24_7", "outdoor_seating", "live_music"]
        for field in vibe_operation_fields:
            if features.get(field) is True:
                conditions.append({field: {"$eq": True}})

        # Construct where filter
        where_filter = None
        if len(conditions) == 1:
            # Single condition - use directly
            where_filter = conditions[0]
        elif len(conditions) > 1:
            # Multiple conditions - use $and operator
            where_filter = {"$and": conditions}

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=k,
                where=where_filter
            )
            # Flatten list of lists
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Retrieval Error: {e}")
            return []

    def generate_advice(self, features):
        start_time = time.time()
        try:
            # A. Retrieve
            reviews = self.retrieve_reviews(features)

            if not reviews:
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
