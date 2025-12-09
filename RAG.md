# RAG System

## Overview

The RAG system provides AI-powered business insights by analyzing real reviews from similar restaurants. When a user describes their planned restaurant, the system retrieves relevant reviews from the chroma database and sends that as context along with the prompt to the LLM.

## How It Works

The system operates in three main stages: data preparation, retrieval, and generation.

### Data Preparation

Restaurant reviews are stored in ChromaDB, a vector database that enables semantic search. Each review is tagged with metadata about the restaurant it belongs to, including category, location, price level, and operational features like outdoor seating or twenty-four hour service. This metadata allows the system to find reviews from restaurants that match the user's planned establishment.

### Retrieval Process

When a user submits their restaurant features, the system employs a three-level filtering strategy to find the most relevant reviews. It starts strict and progressively relaxes the filters if insufficient results are found.

The first level applies all filters: restaurant category, area, price level, and any special features the user selected like outdoor seating or live music. This finds reviews from highly similar establishments.

If too few reviews are found, the second level drops the special features and only matches on category, area, and price level. This broadens the search while maintaining core identity alignment.

The third level, if needed, matches only on restaurant category. This ensures the system can still provide guidance even for unique restaurant configurations.

### Advice Generation

Once relevant reviews are retrieved, they are sent to Google's Gemini language model along with a structured prompt. The prompt includes the user's restaurant features and instructs the model to analyze the reviews for success factors and potential pitfalls. The model generates specific, actionable advice based solely on the patterns it identifies in the retrieved reviews.

### Follow Up Questions

Users can continue the conversation by asking follow-up questions. The system detects whether a question requires searching the database for specific information. Questions containing patterns like "which restaurant", "show me examples", or "what do reviews say about" trigger a semantic search that retrieves fresh reviews directly matching the query. These newly retrieved reviews are added to the conversation context before generating the response, allowing the language model to answer with specific, database-backed information rather than general knowledge.

## Key Features

The system tracks token usage and latency for cost monitoring and performance optimization. It includes guardrails to detect and filter inappropriate content, ensuring safe and relevant responses.

Users can ask follow-up questions through a chat interface that maintains conversation context, allowing them to dive deeper into specific aspects of the advice without repeating their restaurant details.
