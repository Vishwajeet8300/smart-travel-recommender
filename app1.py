import streamlit as st
import pandas as pd
import numpy as np
import joblib
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# ✅ Set page config
st.set_page_config(page_title="Travel Recommender", layout="wide")

# 🎨 Gradient Background with Light/Dark Support
st.markdown(
    """
    <style>
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: linear-gradient(135deg, #1f1c2c 0%, #928dab 100%);
            color: #f0f0f0;
        }
        .block-container {
            background-color: rgba(40, 40, 40, 0.85);
            color: #ffffff;
        }
    }

    @media (prefers-color-scheme: light) {
        .stApp {
            background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
            color: #1a1a1a;
        }
        .block-container {
            background-color: rgba(255, 255, 255, 0.85);
            color: #000000;
        }
    }

    .block-container {
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.15);
        transition: background-color 0.3s ease-in-out, color 0.3s ease-in-out;
    }

    button[kind="primary"] {
        background-color: #ff7e5f;
        color: white;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
    }

    button[kind="primary"]:hover {
        background-color: #feb47b;
        transform: scale(1.03);
    }

    input, textarea, select {
        border-radius: 10px !important;
        padding: 0.5rem !important;
    }

    h1, h2, h3 {
        margin-top: 1.2em;
        margin-bottom: 0.6em;
    }

    a {
        color: #0077cc;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and intro
st.title("✈️ Smart Travel Destination Recommender")
st.markdown("### Select your preferences to discover the top 5 travel destinations in India 🌏")

# ✅ Load model and data
knn_model = joblib.load("knn_model.pkl")
preprocessor = joblib.load("preprocessor.pkl")
df = pd.read_csv("final.csv")

# --- User Input ---
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
            user_input = {
                "Zone": zone,
                "Significance": significance,
                "Airport with 50km Radius": airport_value
            }
            user_df = pd.DataFrame([user_input])
            user_df[["Zone", "Significance"]] = user_df[["Zone", "Significance"]].astype(str)

            user_encoded = preprocessor.transform(user_df)
            distances, indices = knn_model.kneighbors(user_encoded)
            recommendations = df.iloc[indices[0]][[
                "Name", "City", "State", "Type", "Significance", 
                "Entrance Fee in INR", "Google review rating"
            ]]

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

# --- Distance and Cost Estimator ---
st.markdown("---")
st.header("📍 Estimate Travel Distance & Cost")
st.markdown("Enter your **Start Location** and **Destination** to calculate the travel distance and estimated cost:")

# ✅ Retry-safe geocode function
def safe_geocode(geolocator, location, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return geolocator.geocode(location, timeout=10)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise e

# Form inputs
with st.form("distance_form"):
    col1, col2 = st.columns(2)
    with col1:
        source = st.text_input("🚩 Start Location", placeholder="e.g., Delhi")
    with col2:
        destination = st.text_input("🏁 Destination", placeholder="e.g., Jaipur")
    submitted = st.form_submit_button("📏 Calculate")

# Process form submission
if submitted:
    if not source or not destination:
        st.warning("⚠️ Please fill in both Start Location and Destination.")
    else:
        try:
            geolocator = Nominatim(user_agent="smart_travel_recommender_2025", timeout=10)
            source_loc = safe_geocode(geolocator, source)
            dest_loc = safe_geocode(geolocator, destination)

            if source_loc and dest_loc:
                source_coords = (source_loc.latitude, source_loc.longitude)
                dest_coords = (dest_loc.latitude, dest_loc.longitude)

                distance_km = round(geodesic(source_coords, dest_coords).km, 2)

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
                st.error("❌ Could not locate one or both cities. Please use full names or check spelling.")
        except Exception as e:
            st.error("⚠️ Connection issue or service error. Try again later.")
            st.exception(e)  # Optional: shows full error for debugging
