import json

import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Taste Karachi - Restaurant Rating Predictor",
    page_icon="🍽️",
    layout="wide",
)

# API endpoint (will connect to FastAPI service in Docker)
API_URL = "http://fastapi:8000/predict"
INFERENCE_URL = "http://fastapi:8000/inference"

# Title and description
st.title("🍽️ Taste Karachi - Restaurant Rating Predictor")
st.markdown(
    """
Predict restaurant ratings in Karachi based on various features like location, amenities, and services.
Fill in the details below to get a predicted rating for your restaurant!
"""
)

# Create two columns for the form
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Basic Information")

    # Basic categorical features
    area_option = st.selectbox(
        "Area/Location",
        options=[
            "Aram Bagh",
            "Azam Basti",
            "Bahadurabad",
            "Baghdadi",
            "Bahria Town",
            "Buffer Zone",
            "Burns Road",
            "Cantonment",
            "Central Jacob Lines",
            "Central Karachi",
            "Chakiwara",
            "City Railway Colony",
            "Civil Lines",
            "Clifton",
            "Delhi Mercantile Society",
            "DHA",
            "Federal B Area",
            "Frere Town",
            "Gadap Town",
            "Garden East",
            "Gari Khata",
            "Gazdarabad",
            "Gulberg Town",
            "Gulistan-e-Johar",
            "Gulshan-e-Iqbal",
            "I.I. Chundrigar Road",
            "Jamshed Quarters",
            "KAECHS",
            "KDA Scheme 1",
            "Keamari",
            "Kharadar",
            "Khudadad Colony",
            "Korangi",
            "Lalazar",
            "Landhi",
            "Liaquatabad",
            "MACHS",
            "Malir",
            "Mehmoodabad",
            "Model Colony",
            "Nanak Wara",
            "Naval Colony",
            "Nazimabad",
            "New Chali",
            "North Karachi",
            "North Nazimabad",
            "Orangi Town",
            "Pak Colony",
            "PECHS",
            "Preedy Quarters",
            "Rangiwara",
            "Rohail Khand Society",
            "Saddar",
            "Scheme 33",
            "Shah Faisal Town",
            "Shahrah-e-Faisal",
            "Sharfabad",
            "Sindhi Muslim",
            "Soldier Bazaar",
            "Surjani Town",
            "Tariq Road",
            "Tipu Sultan",
            "Urdu Bazaar",
            "Zamzama",
            "Other",
        ],
        index=13,  # Default to "Clifton"
        help="Select the area in Karachi",
    )

    # Show text input if "Other" is selected
    if area_option == "Other":
        area = st.text_input(
            "Enter Custom Area",
            value="",
            help="Enter your area/location",
        )
    else:
        area = area_option

    category_option = st.selectbox(
        "Restaurant Category",
        options=[
            "Restaurant",
            "Fast Food Restaurant",
            "Cafe",
            "Barbecue Restaurant",
            "Chinese Restaurant",
            "Pizza Restaurant",
            "Bakery",
            "Dessert Shop",
            "Indian Restaurant",
            "Buffet Restaurant",
            "Italian Restaurant",
            "Juice Shop",
            "Seafood Restaurant",
            "Korean Restaurant",
            "Breakfast Restaurant",
            "Thai Restaurant",
            "Asian Restaurant",
            "Japanese Restaurant",
            "Middle Eastern Restaurant",
            "American Restaurant",
            "Turkish Restaurant",
            "Fine Dining Restaurant",
            "Food Store",
            "Mediterranean Restaurant",
            "Afghan Restaurant",
            "Event Venue",
            "Wholesaler",
            "Mexican Restaurant",
            "Market",
            "Food Court",
            "Steak House",
            "French Restaurant",
            "Lebanese Restaurant",
            "Other",
        ],
        index=0,
    )

    # Show text input if "Other" is selected
    if category_option == "Other":
        category = st.text_input(
            "Enter Custom Category",
            value="",
            help="Enter your restaurant category",
        )
    else:
        category = category_option

    price_level = st.selectbox(
        "Price Level",
        options=[
            "PRICE_LEVEL_INEXPENSIVE",
            "PRICE_LEVEL_MODERATE",
            "PRICE_LEVEL_EXPENSIVE",
            "PRICE_LEVEL_VERY_EXPENSIVE",
        ],
        index=1,
    )

    st.subheader("🗺️ Estimated Location Coordinates")
    latitude = st.number_input(
        "Latitude",
        min_value=-90.0,
        max_value=90.0,
        value=24.8,
        step=0.1,
        format="%.1f",
    )

    longitude = st.number_input(
        "Longitude",
        min_value=-180.0,
        max_value=180.0,
        value=67.1,
        step=0.1,
        format="%.1f",
    )

with col2:
    st.subheader("🍽️ Services & Amenities")

    # Service options
    st.markdown("**Service Options:**")
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        dine_in = st.checkbox("Dine-in", value=True)
        takeout = st.checkbox("Takeout", value=True)
    with col2_2:
        delivery = st.checkbox("Delivery", value=False)
        reservable = st.checkbox("Reservable", value=True)

    # Meal services
    st.markdown("**Meal Services:**")
    col3_1, col3_2, col3_3 = st.columns(3)
    with col3_1:
        serves_breakfast = st.checkbox("Breakfast", value=False)
        serves_lunch = st.checkbox("Lunch", value=True)
    with col3_2:
        serves_dinner = st.checkbox("Dinner", value=True)
        serves_coffee = st.checkbox("Coffee", value=False)
    with col3_3:
        serves_dessert = st.checkbox("Dessert", value=True)

    # Amenities
    st.markdown("**Amenities:**")
    col4_1, col4_2, col4_3 = st.columns(3)
    with col4_1:
        outdoor_seating = st.checkbox("Outdoor Seating", value=False)
        live_music = st.checkbox("Live Music", value=False)
        restroom = st.checkbox("Restroom", value=True)
    with col4_2:
        good_for_children = st.checkbox("Good for Children", value=True)
        good_for_groups = st.checkbox("Good for Groups", value=True)
        good_for_watching_sports = st.checkbox("Sports Viewing", value=False)
    with col4_3:
        wheelchair_accessible = st.checkbox("Wheelchair Accessible", value=True)

    # Parking
    st.markdown("**Parking:**")
    col5_1, col5_2 = st.columns(2)
    with col5_1:
        parking_free_lot = st.checkbox("Free Parking Lot", value=False)
    with col5_2:
        parking_free_street = st.checkbox("Free Street Parking", value=True)

    # Payment
    st.markdown("**Payment Options:**")
    payment_method = st.radio(
        "Payment Method",
        options=["Accepts Debit Cards", "Cash Only"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )
    accepts_debit_cards = payment_method == "Accepts Debit Cards"
    accepts_cash_only = payment_method == "Cash Only"

    # Operating hours
    st.markdown("**Operating Hours:**")
    col7_1, col7_2, col7_3 = st.columns(3)
    with col7_1:
        is_open_24_7 = st.checkbox("Open 24/7", value=False)
    with col7_2:
        open_after_midnight = st.checkbox("Open After Midnight", value=False)
    with col7_3:
        is_closed_any_day = st.checkbox(
            "Closed Any Day", value=False, disabled=is_open_24_7
        )

    # Disable is_open_24_7 if is_closed_any_day is checked
    if is_closed_any_day:
        is_open_24_7 = False

# Predict button
st.markdown("---")
if st.button("🔮 Predict Rating", type="primary", use_container_width=True):
    # Prepare the data
    restaurant_data = {
        "area": area,
        "price_level": price_level,
        "category": category,
        "latitude": latitude,
        "longitude": longitude,
        "dine_in": dine_in,
        "takeout": takeout,
        "delivery": delivery,
        "reservable": reservable,
        "serves_breakfast": serves_breakfast,
        "serves_lunch": serves_lunch,
        "serves_dinner": serves_dinner,
        "serves_coffee": serves_coffee,
        "serves_dessert": serves_dessert,
        "outdoor_seating": outdoor_seating,
        "live_music": live_music,
        "good_for_children": good_for_children,
        "good_for_groups": good_for_groups,
        "good_for_watching_sports": good_for_watching_sports,
        "restroom": restroom,
        "parking_free_lot": parking_free_lot,
        "parking_free_street": parking_free_street,
        "accepts_debit_cards": accepts_debit_cards,
        "accepts_cash_only": accepts_cash_only,
        "wheelchair_accessible": wheelchair_accessible,
        "is_open_24_7": is_open_24_7,
        "open_after_midnight": open_after_midnight,
        "is_closed_any_day": is_closed_any_day,
    }

    try:
        # Make API request
        response = requests.post(API_URL, json=restaurant_data, timeout=10)

        if response.status_code == 200:
            result = response.json()

            # Display result in a nice format
            st.success("✅ Prediction Successful!")

            # Create metrics display
            col_res1, col_res2, col_res3 = st.columns(3)

            with col_res1:
                st.metric(
                    label="Predicted Rating",
                    value=f"⭐ {result['predicted_rating']}/5",
                )

            with col_res2:
                st.metric(label="Model Version", value=result["model_version"])

            with col_res3:
                st.metric(label="Rating Scale", value=result["rating_scale"])

            # Call RAG inference endpoint and display advice on frontend
            st.markdown("---")
            st.subheader("💡 AI-Generated Business Advice")

            with st.spinner(
                "🤖 Generating personalized advice based on similar restaurants..."
            ):
                try:
                    inference_data = {
                        # Categorical fields
                        "category": category,
                        "area": area,
                        "price_level": price_level,
                        # Boolean fields - pass all from the form
                        "dine_in": dine_in,
                        "takeout": takeout,
                        "delivery": delivery,
                        "reservable": reservable,
                        "serves_breakfast": serves_breakfast,
                        "serves_lunch": serves_lunch,
                        "serves_dinner": serves_dinner,
                        "serves_coffee": serves_coffee,
                        "serves_dessert": serves_dessert,
                        "outdoor_seating": outdoor_seating,
                        "live_music": live_music,
                        "good_for_children": good_for_children,
                        "good_for_groups": good_for_groups,
                        "good_for_watching_sports": good_for_watching_sports,
                        "restroom": restroom,
                        "parking_free_lot": parking_free_lot,
                        "parking_free_street": parking_free_street,
                        "accepts_debit_cards": accepts_debit_cards,
                        "accepts_cash_only": accepts_cash_only,
                        "wheelchair_accessible": wheelchair_accessible,
                        "is_open_24_7": is_open_24_7,
                        "open_after_midnight": open_after_midnight,
                        "is_closed_any_day": is_closed_any_day,
                    }

                    # Print request to terminal
                    print("\n" + "=" * 60)
                    print("RAG INFERENCE API CALL")
                    print("=" * 60)
                    print(f"Category: {category}")
                    print(f"Area: {area}")
                    print(f"Price Level: {price_level}")
                    print(f"Calling: {INFERENCE_URL}")
                    print()

                    inference_response = requests.post(
                        INFERENCE_URL, json=inference_data, timeout=30
                    )

                    # Display results on frontend
                    if inference_response.status_code == 200:
                        inference_result = inference_response.json()
                        advice = inference_result["advice"]

                        # Print to terminal
                        print("✅ RAG Inference SUCCESS!")
                        print(
                            f"Number of reviews retrieved: {inference_result['num_reviews_retrieved']}"
                        )
                        print(f"Status: {inference_result['status']}")
                        print(f"\n{'='*60}")
                        print("GENERATED ADVICE:")
                        print("=" * 60)
                        print(advice)
                        print("=" * 60 + "\n")

                        # Check if fallback message
                        if "No relevant historical reviews found" in advice:
                            st.warning(advice)
                        else:
                            st.info(advice)
                    else:
                        print(
                            f"❌ RAG Inference ERROR: {inference_response.status_code}"
                        )
                        print(f"Response: {inference_response.text}")
                        print("=" * 60 + "\n")
                        st.error(
                            f"Failed to generate advice: {inference_response.status_code}"
                        )

                except Exception as inference_error:
                    print(f"❌ RAG Inference Exception: {str(inference_error)}")
                    print("=" * 60 + "\n")
                    st.error(f"Error generating advice: {str(inference_error)}")

        else:
            st.error(f"❌ Error: {response.status_code}")
            st.code(response.text)

    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Failed to connect to the API. Make sure the FastAPI server is running."
        )
    except requests.exceptions.Timeout:
        st.error("❌ Request timeout. The API is taking too long to respond.")
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")

# Sidebar with additional info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown(
        """
    This application predicts restaurant ratings in Karachi based on various features including:
    - Location and area
    - Price level
    - Category/cuisine type
    - Available services
    - Amenities
    - Operating hours

    **Model:** Restaurant Rating Prediction v1

    **Technology Stack:**
    - FastAPI (Backend)
    - Streamlit (Frontend)
    - MLflow (Model Management)
    - Docker (Containerization)
    """
    )

    st.markdown("---")

    st.header("📖 Quick Tips")
    st.markdown(
        """
    - Fill in all the fields accurately
    - Coordinates should be in Karachi area (approximately lat: 24.8, lon: 67.0)
    - Price levels range from inexpensive to very expensive
    - Check amenities that your restaurant offers
    """
    )

    st.markdown("---")

    # API Health Check
    st.header("🏥 API Status")
    if st.button("Check API Health"):
        try:
            health_response = requests.get("http://fastapi:8000/health", timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                st.success("✅ API is healthy")
                st.json(health_data)
            else:
                st.warning(f"⚠️ API returned status: {health_response.status_code}")
        except Exception as e:
            st.error(f"❌ API is unavailable: {str(e)}")
