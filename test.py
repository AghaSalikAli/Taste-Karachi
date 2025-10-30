# test_prediction.py
import requests
import json

# API endpoint
url = "http://localhost:8000/predict"

# Sample restaurant data
restaurant_data = {
    "area": "Clifton",
    "price_level": "PRICE_LEVEL_MODERATE",
    "category": "Fast Food Restaurant",
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
    "open_after_midnight": True,
    "is_closed_any_day": True
}

# Make request
print("🚀 Testing prediction endpoint...")
print(f"📍 URL: {url}")
print(f"📦 Input: {restaurant_data['area']}, {restaurant_data['category']}, {restaurant_data['price_level']}\n")

try:
    response = requests.post(url, json=restaurant_data)

    if response.status_code == 200:
        result = response.json()
        print("✅ Prediction successful!")
        print(f"⭐ Predicted Rating: {result['predicted_rating']}")
        print(f"📊 Model: {result['model_name']} (version {result['model_version']})")
        print(f"\n📄 Full Response:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Failed to connect: {e}")
    print("💡 Make sure the API is running: python src/api.py")
