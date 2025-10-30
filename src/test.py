# test_prediction.py
import requests
import json

# API endpoint
url = "http://localhost:8000/predict"

# Sample restaurant data
restaurant_data = {
    "area": "Gulshan-e-Iqbal",
    "price_level": "PRICE_LEVEL_EXPENSIVE",
    "category": "Fast Food Restaurant",
    "latitude": 44.8138,
    "longitude": 67.0011,
    "dine_in": True,
    "takeout": True,
    "delivery": True,
    "reservable": True,
    "serves_breakfast": True,
    "serves_lunch": True,
    "serves_dinner": True,
    "serves_coffee": True,
    "serves_dessert": True,
    "outdoor_seating": True,
    "live_music": False,
    "good_for_children": False,
    "good_for_groups": False,
    "good_for_watching_sports": False,
    "restroom": False,
    "parking_free_lot": False,
    "parking_free_street": False,
    "accepts_debit_cards": False,
    "accepts_cash_only": False,
    "wheelchair_accessible": False,
    "is_open_24_7": False,
    "open_after_midnight": False,
    "is_closed_any_day": False
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
