# RAG System Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Golden Subset Filtering Strategy](#golden-subset-filtering-strategy)
4. [Metadata Fields](#metadata-fields)
5. [Implementation Details](#implementation-details)
6. [Testing Guide](#testing-guide)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)
9. [Future Enhancements](#future-enhancements)

---

## Overview

The RAG (Retrieval-Augmented Generation) system enhances the Taste Karachi application by providing AI-powered business insights based on real restaurant reviews. It uses ChromaDB for vector storage and Google's Gemini LLM for generating contextual advice.

### Workflow

1. **User Input**: User fills in restaurant features in Streamlit frontend
2. **Prediction**: FastAPI `/predict` endpoint makes rating prediction
3. **RAG Inference**: FastAPI `/inference` endpoint:
   - Retrieves relevant reviews from ChromaDB using restaurant features
   - Sends reviews as context to Google's Gemini LLM
   - Generates business advice based on real reviews
4. **Output**: Advice is displayed in the terminal and UI

---

## System Architecture

### Files Modified

#### 1. `src/api.py`

- Added `RAGEngine` import
- Added `rag_engine` global variable
- Modified `load_model()` to initialize RAG engine on startup
- Added `/inference` endpoint for RAG-based advice generation
- Updated `/health` endpoint to show RAG engine status

#### 2. `src/streamlit_app.py`

- Added `INFERENCE_URL` constant
- Modified prediction success handler to call `/inference` endpoint
- Shows inference status in UI

#### 3. `src/rag.py`

- `RAGEngine` class with vector database integration
- `retrieve_reviews()` method (queries ChromaDB)
- `generate_advice()` method (calls Gemini LLM)
- Implements Golden Subset filtering logic

---

## Golden Subset Filtering Strategy

The RAG system uses a **Golden Subset** of features for filtering to prevent over-filtering and ensure better retrieval results.

### The Golden Subset

#### 1. Strict Identity Filters (Always Applied)

These define **WHAT** the business is:

| Field         | Description     | Example                                         |
| ------------- | --------------- | ----------------------------------------------- |
| `category`    | Restaurant type | "Chinese Restaurant", "Fast Food Restaurant"    |
| `area`        | Location        | "Clifton", "DHA", "Gulshan"                     |
| `price_level` | Price range     | "PRICE_LEVEL_MODERATE", "PRICE_LEVEL_EXPENSIVE" |

**Behavior**: Always included in the filter. These are mandatory to match the core identity.

#### 2. Vibe/Operation Filters (Conditionally Applied)

These define **HOW** it operates:

| Field             | Description         | Filter Logic          |
| ----------------- | ------------------- | --------------------- |
| `is_open_24_7`    | 24/7 operation      | Only filter if `True` |
| `outdoor_seating` | Has outdoor seating | Only filter if `True` |
| `live_music`      | Offers live music   | Only filter if `True` |

**Behavior**: Only included in filter if user sets them to `True`. This adds vibe/atmosphere specificity without being too restrictive.

### Why This Approach?

#### Problem with Full Filtering

Using all 26 metadata fields for filtering causes:

- ❌ Over-filtering - Too restrictive, returns few or no results
- ❌ Exact matching - Requires restaurants to match ALL features
- ❌ Poor user experience - Empty results frustrate users

#### Benefits of Golden Subset

- ✅ **Better recall**: More relevant reviews returned
- ✅ **Smart specificity**: Core features matched, optional vibe added
- ✅ **Balanced results**: 5-10 quality reviews instead of 0-2
- ✅ **Flexibility**: Users can add vibe filters as needed

### Filtering Examples

#### Example 1: Basic Identity Only

```python
features = {
    "category": "Chinese Restaurant",
    "area": "Clifton",
    "price_level": "PRICE_LEVEL_MODERATE",
    "is_open_24_7": False,        # Not filtered
    "outdoor_seating": False,     # Not filtered
    "live_music": False           # Not filtered
}
# Filter: category + area + price_level
# Returns: All Chinese restaurants in Clifton with moderate pricing
```

#### Example 2: Identity + Vibe

```python
features = {
    "category": "Chinese Restaurant",
    "area": "Clifton",
    "price_level": "PRICE_LEVEL_MODERATE",
    "is_open_24_7": False,        # Not filtered
    "outdoor_seating": True,      # FILTERED! ✓
    "live_music": False           # Not filtered
}
# Filter: category + area + price_level + outdoor_seating=True
# Returns: Chinese restaurants in Clifton (moderate) WITH outdoor seating
```

#### Example 3: Identity + Multiple Vibes

```python
features = {
    "category": "Fine Dining Restaurant",
    "area": "DHA",
    "price_level": "PRICE_LEVEL_EXPENSIVE",
    "is_open_24_7": False,
    "outdoor_seating": True,      # FILTERED! ✓
    "live_music": True            # FILTERED! ✓
}
# Filter: category + area + price_level + outdoor_seating + live_music
# Returns: Fine dining in DHA (expensive) WITH outdoor seating AND live music
```

---

## Metadata Fields

### All Fields (26 Total)

#### Categorical Fields (3)

- `category` - Restaurant type (Chinese, Fast Food, etc.)
- `area` - Location (Clifton, DHA, etc.)
- `price_level` - Price range (MODERATE, EXPENSIVE, etc.)

#### Boolean Fields (23)

**Golden Subset (Used for Filtering):**

- `is_open_24_7` - 24/7 operation
- `outdoor_seating` - Has outdoor seating
- `live_music` - Offers live music

**Other Fields (Not Used for Filtering):**

- **Service Options**: `dine_in`, `takeout`, `delivery`, `reservable`
- **Meals**: `serves_breakfast`, `serves_lunch`, `serves_dinner`, `serves_coffee`, `serves_dessert`
- **Amenities**: `restroom`
- **Suitability**: `good_for_children`, `good_for_groups`, `good_for_watching_sports`
- **Parking**: `parking_free_lot`, `parking_free_street`
- **Payment**: `accepts_debit_cards`, `accepts_cash_only`
- **Accessibility**: `wheelchair_accessible`
- **Hours**: `open_after_midnight`, `is_closed_any_day`

### Field Usage

All 26 fields are:

- ✅ Sent to API
- ✅ Stored in request
- ⚠️ Only 6 used for filtering (Golden Subset)
- 💡 Others available for future use (analytics, recommendations, etc.)

---

## Implementation Details

### ChromaDB Query Structure

#### Single Identity Filter

```python
where_filter = {"category": {"$eq": "Chinese Restaurant"}}
```

#### Multiple Filters (Using $and)

```python
where_filter = {
    "$and": [
        {"category": {"$eq": "Chinese Restaurant"}},
        {"area": {"$eq": "Clifton"}},
        {"price_level": {"$eq": "PRICE_LEVEL_MODERATE"}},
        {"outdoor_seating": {"$eq": True}}
    ]
}
```

### RAG Engine Implementation (`src/rag.py`)

```python
def retrieve_reviews(self, features, k=5):
    conditions = []

    # 1. STRICT IDENTITY (Always)
    for field in ["category", "area", "price_level"]:
        if features.get(field):
            conditions.append({field: {"$eq": features.get(field)}})

    # 2. VIBE/OPERATION (Only if True)
    for field in ["is_open_24_7", "outdoor_seating", "live_music"]:
        if features.get(field) is True:
            conditions.append({field: {"$eq": True}})

    # Build where filter
    where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    # Query ChromaDB
    results = self.collection.query(
        query_texts=[query_text],
        n_results=k,
        where=where_filter
    )
    return results
```

---

## Testing Guide

### Prerequisites

```bash
# Ensure .env file has GOOGLE_API_KEY
echo "GOOGLE_API_KEY=your_key_here" > .env
```

### Option 1: Test RAG Module Directly

```bash
# Activate virtual environment
source mlops/bin/activate

# Run the test script
python src/test_rag_local.py
```

### Option 2: Test API Endpoint

```bash
# Activate virtual environment
source mlops/bin/activate

# Run the API test script
python test_inference_api.py
```

### Option 3: Test Full Stack (with Docker)

```bash
# Start Docker services
docker-compose -f docker-compose.dev.yml up --build

# Access Streamlit at http://localhost:8501
# Access API docs at http://localhost:8000/docs
```

### Expected Output

#### Terminal Output on Prediction

```
============================================================
RAG INFERENCE REQUEST
============================================================
Category: Chinese Restaurant
Area: Clifton
Price Level: PRICE_LEVEL_MODERATE
============================================================

[1/2] Retrieving relevant reviews from ChromaDB...
✓ Retrieved 5 reviews

[2/2] Generating advice using LLM...
✓ Generated advice

============================================================
GENERATED ADVICE:
============================================================
Key Success Factors:
1. Authentic Taste & High Quality
2. Generous Portions at Reasonable Prices
3. Excellent Service

Potential Pitfall:
1. Outdated Ambiance/High Prices
============================================================
```

#### Streamlit UI

- Shows "🧠 Generating business insights using RAG..."
- On success: "✅ Business insights generated! (Check terminal for details)"
- Shows inference details (number of reviews, status)

---

## API Reference

### Environment Variables

```bash
GOOGLE_API_KEY=your_google_api_key_here
CHROMA_DB_PATH=./chroma_db_data  # Optional, defaults to this
```

### Endpoints

#### `/predict` (POST)

**Purpose**: Make rating prediction

**Input**: Full restaurant features (29+ fields)

**Output**: Predicted rating (0-5)

#### `/inference` (POST)

**Purpose**: Generate business advice using RAG

**Input**:

```json
{
  "category": "Chinese Restaurant",
  "area": "Clifton",
  "price_level": "PRICE_LEVEL_MODERATE",
  "is_open_24_7": false,
  "outdoor_seating": true,
  "live_music": false,
  "dine_in": true,
  "takeout": true
  // ... other fields
}
```

**Output**:

```json
{
    "advice": "...",
    "num_reviews_retrieved": 5,
    "features_used": {...},
    "status": "success"
}
```

#### `/health` (GET)

**Purpose**: Check service health

**Output**:

```json
{
    "status": "healthy",
    "model_loaded": true,
    "rag_engine_loaded": true,
    "model_info": {...}
}
```

---

## Troubleshooting

### RAG Engine fails to initialize

- Check if `GOOGLE_API_KEY` is set in `.env`
- Verify ChromaDB path exists and has data
- Check if langchain packages are installed

### No reviews retrieved

- Verify ChromaDB has data in `restaurant_reviews` collection
- Check if category filter matches existing data
- Try removing vibe filters (set to `False`)
- Consider broadening the search area

### LLM errors

- Verify Google API key is valid
- Check internet connectivity
- Verify model name is correct (`gemini-2.0-flash` or `gemini-pro`)
- Check API quota/rate limits

### Over-filtering issues

If you consistently get no results:

- Ensure only Golden Subset fields are being filtered
- Check that vibe filters (`is_open_24_7`, `outdoor_seating`, `live_music`) are only applied when `True`
- Verify ChromaDB has sufficient data for the category/area combination

---

## Future Enhancements

### Potential Additions to Golden Subset

Consider adding if over-filtering persists:

- `delivery` - Increasingly important filter
- `good_for_groups` - Common use case
- `wheelchair_accessible` - Accessibility requirement

### Dynamic Golden Subset

Could implement:

- User preference for filter strictness
- AI-learned golden subset based on query success
- Category-specific golden subsets (fast food vs fine dining)

### UI Enhancements

To display advice in the UI:

1. Modify Streamlit app to show advice in an expander
2. Add advice to the prediction response
3. Create a separate "Get Advice" button
4. Add feedback mechanism for advice quality

### Advanced Features

- Multi-language support for advice generation
- Historical tracking of advice effectiveness
- A/B testing different prompt strategies
- Integration with business metrics (success rate correlation)

---

## Summary

**Golden Subset = Core Identity (3) + Optional Vibe (3)**

This approach balances:

- 🎯 **Precision**: Matches core restaurant type and location
- 📊 **Recall**: Returns sufficient reviews for quality LLM context
- 🎨 **Flexibility**: Users can optionally add vibe/atmosphere filters
- ⚡ **Performance**: Faster queries with fewer filter conditions

**Result**: Better, more relevant business advice based on appropriate restaurant reviews!
