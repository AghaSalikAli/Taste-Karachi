# src/api.py

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from pydantic import BaseModel, Field
import mlflow
import mlflow.pyfunc
import pandas as pd
from pathlib import Path
import uvicorn
from typing import Literal, Optional
import os

# Import RAG Engine
from src.rag import RAGEngine

# ============================================
# MLflow Configuration
# ============================================
# Set MLflow tracking URI to your server
MLFLOW_TRACKING_URI = "http://54.226.237.246:5000"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Model Registry Configuration
MODEL_NAME = "Restaurant_rating_prediction_regression"
MODEL_VERSION = "1"

# Initialize FastAPI
app = FastAPI(
    title="Taste Karachi - Restaurant Rating Predictor",
    description="Predict restaurant ratings in Karachi based on features",
    version="1.0.0",
)


# Initialize Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Load model at startup
MODEL_PATH = Path(__file__).parent.parent / "models"


# Global model variable
model = None
model_info = {}
rag_engine = None


@app.on_event("startup")
async def load_model():
    """Load ML model from MLflow Model Registry on startup"""
    global model, model_info, rag_engine
    try:
        # Load model from MLflow Model Registry
        model_uri = f"models:/{MODEL_NAME}/{MODEL_VERSION}"

        print(f"Loading model from MLflow Registry...")
        print(f"Model URI: {model_uri}")

        model = mlflow.pyfunc.load_model(model_uri)

        # Store model info
        model_info = {"name": MODEL_NAME, "version": MODEL_VERSION, "uri": model_uri}

        print(f"✅ Model loaded successfully from registry!")
        print(f"   Model: {MODEL_NAME}")
        print(f"   Version: {MODEL_VERSION}")

        # Initialize RAG Engine
        print(f"\nInitializing RAG Engine...")
        try:
            rag_engine = RAGEngine()
            print(f"✅ RAG Engine initialized successfully!")
        except Exception as rag_error:
            print(f"⚠️ Warning: RAG Engine failed to initialize: {rag_error}")
            print(f"   Inference endpoint will not be available.")
            rag_engine = None

    except Exception as e:
        print(f"❌ Error loading model from registry: {e}")
        print(f"   Make sure:")
        print(f"   1. MLflow server is running at {MLFLOW_TRACKING_URI}")
        print(f"   2. Model '{MODEL_NAME}' exists in the registry")
        print(f"   3. Version '{MODEL_VERSION}' exists")
        raise e


# Define RAG inference input schema
class InferenceRequest(BaseModel):
    """Request schema for RAG inference"""

    # Categorical fields
    category: str = Field(..., description="Restaurant category")
    area: str = Field(..., description="Restaurant area/location")
    price_level: str = Field(..., description="Price level")

    # Boolean fields - all optional
    dine_in: Optional[bool] = Field(False, description="Offers dine-in service")
    takeout: Optional[bool] = Field(False, description="Offers takeout service")
    delivery: Optional[bool] = Field(False, description="Offers delivery service")
    reservable: Optional[bool] = Field(False, description="Accepts reservations")
    serves_breakfast: Optional[bool] = Field(False, description="Serves breakfast")
    serves_lunch: Optional[bool] = Field(False, description="Serves lunch")
    serves_dinner: Optional[bool] = Field(False, description="Serves dinner")
    serves_coffee: Optional[bool] = Field(False, description="Serves coffee")
    serves_dessert: Optional[bool] = Field(False, description="Serves dessert")
    outdoor_seating: Optional[bool] = Field(False, description="Has outdoor seating")
    live_music: Optional[bool] = Field(False, description="Has live music")
    good_for_children: Optional[bool] = Field(False, description="Good for children")
    good_for_groups: Optional[bool] = Field(False, description="Good for groups")
    good_for_watching_sports: Optional[bool] = Field(
        False, description="Good for watching sports"
    )
    restroom: Optional[bool] = Field(False, description="Has restroom")
    parking_free_lot: Optional[bool] = Field(False, description="Free parking lot")
    parking_free_street: Optional[bool] = Field(
        False, description="Free street parking"
    )
    accepts_debit_cards: Optional[bool] = Field(
        False, description="Accepts debit cards"
    )
    accepts_cash_only: Optional[bool] = Field(False, description="Cash only")
    wheelchair_accessible: Optional[bool] = Field(
        False, description="Wheelchair accessible"
    )
    is_open_24_7: Optional[bool] = Field(False, description="Open 24/7")
    open_after_midnight: Optional[bool] = Field(
        False, description="Open after midnight"
    )
    is_closed_any_day: Optional[bool] = Field(False, description="Closed any day")

    class Config:
        schema_extra = {
            "example": {
                "category": "Chinese Restaurant",
                "area": "Clifton",
                "price_level": "PRICE_LEVEL_MODERATE",
                "dine_in": True,
                "takeout": True,
                "delivery": False,
                "serves_lunch": True,
                "serves_dinner": True,
            }
        }


# Define input schema matching your features
class RestaurantFeatures(BaseModel):
    """Restaurant features for rating prediction"""

    # Categorical features
    area: str = Field(..., description="Restaurant area/location in Karachi")
    price_level: str = Field(
        ...,
        description="Price level (e.g., PRICE_LEVEL_MODERATE, PRICE_LEVEL_INEXPENSIVE, PRICE_LEVEL_EXPENSIVE, PRICE_LEVEL_VERY_EXPENSIVE)",
    )
    category: str = Field(
        ...,
        description="Restaurant category/type (e.g., Restaurant, Fast Food Restaurant, Cafe, etc.)",
    )

    # Numeric features
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")

    # Binary features (amenities)
    dine_in: bool = Field(..., description="Offers dine-in service")
    takeout: bool = Field(..., description="Offers takeout service")
    delivery: bool = Field(..., description="Offers delivery service")
    reservable: bool = Field(..., description="Accepts reservations")

    # Meal services
    serves_breakfast: bool
    serves_lunch: bool
    serves_dinner: bool
    serves_coffee: bool
    serves_dessert: bool

    # Amenities
    outdoor_seating: bool
    live_music: bool
    good_for_children: bool
    good_for_groups: bool
    good_for_watching_sports: bool
    restroom: bool

    # Parking
    parking_free_lot: bool
    parking_free_street: bool

    # Payment
    accepts_debit_cards: bool
    accepts_cash_only: bool

    # Accessibility
    wheelchair_accessible: bool

    # Operating hours
    is_open_24_7: bool
    open_after_midnight: bool
    is_closed_any_day: bool

    class Config:
        schema_extra = {
            "example": {
                "area": "Clifton",
                "price_level": "PRICE_LEVEL_MODERATE",
                "category": "Restaurant",
                "latitude": 24.8138,
                "longitude": 67.0011,
                "dine_in": True,
                "takeout": True,
                "delivery": False,
                "reservable": True,
                "serves_breakfast": False,
                "serves_lunch": True,
                "serves_dinner": True,
                "serves_coffee": False,
                "serves_dessert": True,
                "outdoor_seating": False,
                "live_music": False,
                "good_for_children": True,
                "good_for_groups": True,
                "good_for_watching_sports": False,
                "restroom": True,
                "parking_free_lot": False,
                "parking_free_street": True,
                "accepts_debit_cards": True,
                "accepts_cash_only": False,
                "wheelchair_accessible": True,
                "is_open_24_7": False,
                "open_after_midnight": False,
                "is_closed_any_day": False,
            }
        }


# Root endpoint
@app.get("/")
def root():
    """API information and available endpoints"""
    return {
        "message": "Welcome to Taste Karachi Restaurant Rating Prediction API",
        "description": "Predict restaurant ratings based on features",
        "version": "1.0.0",
        "model": model_info,
        "mlflow_server": MLFLOW_TRACKING_URI,
        "endpoints": {
            "health": "/health - Health check",
            "predict": "/predict - Make predictions",
            "model_info": "/model-info - Get model details",
            "docs": "/docs - Interactive API documentation",
            "openapi": "/openapi.json - OpenAPI specification",
        },
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "rag_engine_loaded": rag_engine is not None,
        "model_info": model_info,
    }


# New endpoint: Model info
@app.get("/model-info")
def get_model_info():
    """Get information about the loaded model"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model_name": model_info.get("name"),
        "model_version": model_info.get("version"),
        "model_uri": model_info.get("uri"),
        "mlflow_tracking_uri": MLFLOW_TRACKING_URI,
    }


# Prediction endpoint
@app.post("/predict")
def predict_rating(features: RestaurantFeatures):
    """
    Predict restaurant rating based on input features

    Returns predicted rating on a scale of 0-5
    """
    if model is None:
        raise HTTPException(
            status_code=503, detail="Model not loaded. Service unavailable."
        )

    try:
        # Convert Pydantic model to dict then DataFrame
        # Handle both Pydantic v1 and v2
        if hasattr(features, "model_dump"):
            input_dict = features.model_dump()  # Pydantic v2
        else:
            input_dict = features.dict()  # Pydantic v1

        input_df = pd.DataFrame([input_dict])

        # Make prediction
        prediction = model.predict(input_df)
        predicted_rating = float(prediction[0])

        # Clip rating to valid range [0, 5]
        predicted_rating = max(0.0, min(5.0, predicted_rating))

        return {
            "predicted_rating": round(predicted_rating, 2),
            "rating_scale": "0-5",
            "model_name": model_info.get("name"),
            "model_version": model_info.get("version"),
            "input_features": {
                "area": features.area,
                "price_level": features.price_level,
                "category": features.category,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


# RAG Inference endpoint
@app.post("/inference")
def generate_inference(request: InferenceRequest):
    """
    Generate business advice using RAG (Retrieval-Augmented Generation)

    This endpoint:
    1. Retrieves relevant reviews from ChromaDB based on restaurant features
    2. Uses an LLM to generate actionable business advice

    Returns advice for restaurant owners based on similar restaurants
    """
    if rag_engine is None:
        raise HTTPException(
            status_code=503,
            detail="RAG Engine not initialized. Check server logs for details.",
        )

    try:
        # Convert request to features dict for RAG - include all fields
        features = {
            # Categorical
            "category": request.category,
            "area": request.area,
            "price_level": request.price_level,
            # Boolean fields
            "dine_in": request.dine_in,
            "takeout": request.takeout,
            "delivery": request.delivery,
            "reservable": request.reservable,
            "serves_breakfast": request.serves_breakfast,
            "serves_lunch": request.serves_lunch,
            "serves_dinner": request.serves_dinner,
            "serves_coffee": request.serves_coffee,
            "serves_dessert": request.serves_dessert,
            "outdoor_seating": request.outdoor_seating,
            "live_music": request.live_music,
            "good_for_children": request.good_for_children,
            "good_for_groups": request.good_for_groups,
            "good_for_watching_sports": request.good_for_watching_sports,
            "restroom": request.restroom,
            "parking_free_lot": request.parking_free_lot,
            "parking_free_street": request.parking_free_street,
            "accepts_debit_cards": request.accepts_debit_cards,
            "accepts_cash_only": request.accepts_cash_only,
            "wheelchair_accessible": request.wheelchair_accessible,
            "is_open_24_7": request.is_open_24_7,
            "open_after_midnight": request.open_after_midnight,
            "is_closed_any_day": request.is_closed_any_day,
        }

        print(f"\n{'='*60}")
        print(f"RAG INFERENCE REQUEST")
        print(f"{'='*60}")
        print(f"Category: {request.category}")
        print(f"Area: {request.area}")
        print(f"Price Level: {request.price_level}")

        # Show active GOLDEN SUBSET vibe/operation features
        golden_vibe_features = []
        if features.get("is_open_24_7"):
            golden_vibe_features.append("is_open_24_7")
        if features.get("outdoor_seating"):
            golden_vibe_features.append("outdoor_seating")
        if features.get("live_music"):
            golden_vibe_features.append("live_music")

        if golden_vibe_features:
            print(f"Golden Subset Filters: {', '.join(golden_vibe_features)}")
        else:
            print(f"Golden Subset Filters: None (identity only)")
        print(f"{'='*60}\n")

        # Retrieve relevant reviews
        print(f"[1/2] Retrieving relevant reviews from ChromaDB...")
        reviews = rag_engine.retrieve_reviews(features, k=5)
        print(f"✓ Retrieved {len(reviews)} reviews\n")

        # Generate advice using LLM
        print(f"[2/2] Generating advice using LLM...")
        advice = rag_engine.generate_advice(features)
        print(f"✓ Generated advice\n")

        print(f"{'='*60}")
        print(f"GENERATED ADVICE:")
        print(f"{'='*60}")
        print(advice)
        print(f"{'='*60}\n")

        return {
            "advice": advice,
            "num_reviews_retrieved": len(reviews),
            "features_used": features,
            "status": "success",
        }

    except Exception as e:
        print(f"\n❌ ERROR in inference: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


# Run with uvicorn if called directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
