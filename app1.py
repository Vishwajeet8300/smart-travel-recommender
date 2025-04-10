import streamlit as st
import pandas as pd
import numpy as np
import joblib
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ✅ Set page config only once
st.set_page_config(page_title="Travel Recommender", layout="wide")

# 🎨 Gradient Background
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
        background-attachment: fixed;
        background-size: cover;
    }
    .block-container {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and instructions
st.title("✈️ Smart Travel Destination Recommender")
st.markdown("### Select your preferences to discover the top 5 travel destinations in India 🌏")

# ✅ Load models and data
knn_model = joblib.load("knn_model.pkl")
preprocessor = joblib.load("preprocessor.pkl")
df = pd.read_csv("final.csv")

# --- Input Section ---
with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        zone_options = ["-- Select --", "Northern", "Central", "Southern", "Western", "Eastern", "North-East"]
        zone = st.selectbox("🌍 Select Zone", zone_options)

    with col2:
        significance_options = ["-- Select --", "Historical", "Religious", "Environmental", "Scientific", "Market", 
            "Botanical", "Artistic", "Scenic", "Wildlife", "Recreational", "Nature", 
            "Architectural", "Entertainment", "Sports", "Educational", "Cultural", 
            "Food", "Spiritual", "Archaeological", "Adventure", "Agricultural", 
            "Engineering Marvel", "Natural Wonder", "Trekking", "Shopping"]
        significance = st.selectbox("🏛️ Select Significance", significance_options)

    with col3:
        airport = st.radio("✈️ Airport within 50 km?", ["Yes", "No"], horizontal=True)
        airport_value = 1.0 if airport == "Yes" else 0.0

# --- Recommendation Logic ---
if st.button("🎯 Recommend Places"):
    if zone == "-- Select --" or significance == "-- Select --":
        st.warning("⚠️ Please select both Zone and Significance before continuing.")
    else:
        with st.spinner("Finding your perfect destinations..."):
            # Prepare input
            user_input = {
                "Zone": zone,
                "Significance": significance,
                "Airport with 50km Radius": airport_value
            }
            user_df = pd.DataFrame([user_input])
            user_df[["Zone", "Significance"]] = user_df[["Zone", "Significance"]].astype(str)

            # Transform input and get predictions
            user_encoded = preprocessor.transform(user_df)
            distances, indices = knn_model.kneighbors(user_encoded)
            recommendations = df.iloc[indices[0]][[
                "Name", "City", "State", "Type", "Significance", 
                "Entrance Fee in INR", "Google review rating"
            ]]

        # --- Display Results ---
        st.markdown("## 🎉 Top 5 Recommended Destinations")

        for i, row in recommendations.reset_index(drop=True).iterrows():
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {i+1}. {row['Name']} ({row['Type']})")
                st.markdown(f"📍 **Location:** {row['City']}, {row['State']}  \n"
                            f"🏛️ **Significance:** {row['Significance']}  \n"
                            f"💰 **Entrance Fee:** ₹{row['Entrance Fee in INR']}  \n"
                            f"⭐ **Rating:** {row['Google review rating']}/5.0")
            with col2:
                place = f"{row['Name']}, {row['City']}, {row['State']}"
                st.markdown(f"[📌 View on Map](https://www.google.com/maps/search/{place.replace(' ', '+')})")

# --- Distance & Cost Estimator ---
st.markdown("---")
st.header("📍 Estimate Travel Distance & Cost")

st.markdown("Enter your **Start Location** and **Destination** to calculate the travel distance and estimated cost:")

with st.form("distance_form"):
    col1, col2 = st.columns(2)
    with col1:
        source = st.text_input("🚩 Start Location", placeholder="e.g., Delhi")
    with col2:
        destination = st.text_input("🏁 Destination", placeholder="e.g., Jaipur")
    
    submitted = st.form_submit_button("📏 Calculate")

if submitted:
    if not source or not destination:
        st.warning("⚠️ Please fill in both Start Location and Destination.")
    else:
        try:
            geolocator = Nominatim(user_agent="travel_app")
            source_loc = geolocator.geocode(source)
            dest_loc = geolocator.geocode(destination)

            if source_loc and dest_loc:
                source_coords = (source_loc.latitude, source_loc.longitude)
                dest_coords = (dest_loc.latitude, dest_loc.longitude)

                distance_km = geodesic(source_coords, dest_coords).km
                distance_km = round(distance_km, 2)

                # Cost estimation
                car_cost = round(distance_km * 12, 2)
                bus_cost = round(distance_km * 5, 2)
                train_cost = round(distance_km * 2, 2)

                st.success(f"📏 Distance: **{distance_km} km**")

                st.markdown("### 💸 Estimated Travel Cost:")
                st.markdown(f"- 🚗 **Car:** ₹{car_cost}")
                st.markdown(f"- 🚌 **Bus:** ₹{bus_cost}")
                st.markdown(f"- 🚆 **Train:** ₹{train_cost}")
            else:
                st.error("❌ Unable to locate one or both places. Try using full city names or check spelling.")
        except Exception as e:
            st.error(f"⚠️ Error occurred: {e}")
