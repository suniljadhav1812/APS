import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, date

st.set_page_config(page_title="APS Tool", layout="wide")

TEMP_FILE = "temp_user_data.json"

# Load prerequisites
def load_prerequisites():
    try:
        with open("Precision_tables/prerequisites.txt", "r") as f:
            return f.read()
    except:
        return "Prerequisites file not found."

def save_user_data(data):
    with open(TEMP_FILE, "w") as f:
        json.dump(data, f)

st.title("🧪 APS Tool (Accuracy · Precision · Stability)")

with st.sidebar:
    st.header("🧾 User Info")

    username = st.text_input("Name")
    bench_no = st.text_input("Bench No")
    lsd = st.date_input("Last Standardization Date", max_value=date.today())

    # Load base & matrix options
    try:
        base_data = pd.read_excel("Precision_tables/Database_base_matrix.xlsx", sheet_name=None)
        base_options = list(base_data.keys())
    except:
        base_data = {}
        base_options = []

    base = st.selectbox("Select Base", base_options)
    matrix = st.selectbox("Select Matrix", base_data.get(base, pd.DataFrame()).columns if base else [])

    # Load model
    try:
        model_data = pd.read_excel("Precision_tables/Database_Models.xlsx", sheet_name=None)
        model_options = list(model_data.keys())
    except:
        model_data = {}
        model_options = []

    model = st.selectbox("Select Model", model_options)

st.subheader("📌 Prerequisites")
st.text_area("Checklist", load_prerequisites(), height=280, disabled=True)

st.subheader("✅ Checklist Confirmation")
col1, col2 = st.columns(2)
check_stab = col1.checkbox("Stabilization")
check_maint = col1.checkbox("Routine Maintenance")
check_err = col2.checkbox("Error-Free Operation")
check_prep = col2.checkbox("Sample Preparation")

valid = all([username, bench_no, base, matrix, model])

if valid:
    user_data = {
        "username": username,
        "bench_no": bench_no,
        "lsd": lsd.strftime("%d-%m-%Y"),
        "base": base,
        "matrix": matrix,
        "model": model,
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "checklist": {
            "stabilization": check_stab,
            "maintenance": check_maint,
            "error_free": check_err,
            "preparation": check_prep
        }
    }

    save_user_data(user_data)

    colA, colB = st.columns(2)
    with colA:
        st.success("✅ All set! You may proceed.")
        st.page_link("pages/1_Accuracy_and_Precision.py", label="➡️ Accuracy & Precision Test", icon="🧪")

    with colB:
        st.page_link("pages/2_Stability_Test.py", label="📈 Stability Test", icon="📊")
else:
    st.warning("⚠️ Please fill in all fields above and check confirmation boxes.")
