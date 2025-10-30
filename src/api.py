# src/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import mlflow.pyfunc
import pandas as pd
from pathlib import Path
import uvicorn
from typing import Literal

# Initialize FastAPI
app = FastAPI(
    title="Taste Karachi - Restaurant Rating Predictor",
    description="Predict restaurant ratings in Karachi based on features",
    version="1.0.0"
)

# Load model at startup
MODEL_PATH = Path(__file__).parent.parent / "models"
model = None

@app.on_event("startup")
async def load_model():
    """Load ML model on startup"""
    global model
    try:
        model = mlflow.pyfunc.load_model(str(MODEL_PATH))
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise e


# Define input schema matching your features
class RestaurantFeatures(BaseModel):
    """Restaurant features for rating prediction"""

    # Categorical features
    area: str = Field(..., description="Restaurant area/location in Karachi")
    price_level: str = Field(..., description="Price level (e.g., PRICE_LEVEL_MODERATE, PRICE_LEVEL_INEXPENSIVE, PRICE_LEVEL_EXPENSIVE, PRICE_LEVEL_VERY_EXPENSIVE)")
    category: str = Field(..., description="Restaurant category/type (e.g., Restaurant, Fast Food Restaurant, Cafe, etc.)")

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
                "category": "Pakistani",
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
                "is_closed_any_day": False
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
        "model": "Restaurant_rating_prediction_regression v1",
        "endpoints": {
            "health": "/health - Health check",
            "predict": "/predict - Make predictions",
            "docs": "/docs - Interactive API documentation",
            "openapi": "/openapi.json - OpenAPI specification"
        }
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_name": "Restaurant_rating_prediction_regression",
        "version": "v1"
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
            status_code=503,
            detail="Model not loaded. Service unavailable."
        )

    try:
        # Convert Pydantic model to dict then DataFrame
        input_dict = features.model_dump()
        input_df = pd.DataFrame([input_dict])

        # Make prediction
        prediction = model.predict(input_df)
        predicted_rating = float(prediction[0])

        # Clip rating to valid range [0, 5]
        predicted_rating = max(0.0, min(5.0, predicted_rating))

        return {
            "predicted_rating": round(predicted_rating, 2),
            "rating_scale": "0-5",
            "model_version": "v1",
            "model_name": "Restaurant_rating_prediction_regression",
            "input_features": {
                "area": features.area,
                "price_level": features.price_level,
                "category": features.category
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


# Run with uvicorn if called directly
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
