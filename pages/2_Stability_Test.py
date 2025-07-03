import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Stability Test", layout="wide")
st.title("📈 Stability Test (Short / Long Term)")

TEMP_FILE = "temp_user_data.json"

# Load saved user data
def load_user_data():
    try:
        with open(TEMP_FILE, "r") as f:
            return json.load(f)
    except:
        st.error("User info not found. Please complete setup from main page.")
        st.stop()

user_data = load_user_data()
base = user_data["base"]
matrix = user_data["matrix"]
model = user_data["model"]
username = user_data["username"]
lsd = user_data["lsd"]

st.markdown(f"**User:** {username} | **Bench No:** {user_data['bench_no']} | **Model:** {model} | **LSD:** {lsd}")

st.radio("Select Stability Type", ["ShortTerm", "LongTerm"], horizontal=True, key="stab_type")

uploaded_file = st.file_uploader("Upload Stability Report (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    st.success("Stability report loaded. Analysis logic coming soon...")
    # Placeholder: you'll later load data, parse sets, and compute deviation
