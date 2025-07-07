import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, date
import numpy as np
from difflib import get_close_matches
import io
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

prereq_text = load_prerequisites()

st.markdown(
    f"""
    <div style="background-color:#f9f9f9; padding:15px; border-radius:8px; border:1px solid #ddd; max-height:300px; overflow-y:scroll;">
    <pre style="font-size:15px; color:#222;">{prereq_text}</pre>
    </div>
    """,
    unsafe_allow_html=True
)


st.subheader("✅ Checklist Confirmation")
col1, col2 = st.columns(2)

stab = col1.radio("Stabilization", ["No", "Yes"], horizontal=True)
maint = col1.radio("Routine Maintenance", ["No", "Yes"], horizontal=True)
diag = col2.radio("Diagnostics", ["No", "Yes"], horizontal=True)
prep = col2.radio("Sample Preparation", ["No", "Yes"], horizontal=True)

# Determine if at least one checklist item is marked "Yes"
checklist_ok = any([stab == "Yes", maint == "Yes", diag == "Yes", prep == "Yes"])


valid = all([username, bench_no, base, matrix, model])

if valid and checklist_ok:
    user_data = {
        "username": username,
        "bench_no": bench_no,
        "lsd": lsd.strftime("%d-%m-%Y"),
        "base": base,
        "matrix": matrix,
        "model": model,
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "checklist": {
            "stabilization": stab,
            "maintenance": maint,
            "Diagnostics": diag,
            "preparation": prep
        }
    }

    save_user_data(user_data)
    log_user_data(user_data)  # ✅ This is where you put it

    colA, colB = st.columns(2)
    with colA:
        st.success("✅ All set! You may proceed.")
        st.page_link("pages/1_Accuracy_and_Precision.py", label="➡️ Accuracy & Precision Test", icon="🧪")

    with colB:
        st.page_link("pages/2_Stability_Test.py", label="📈 Stability Test", icon="📊")
else:
    st.warning("⚠️ Please fill in all fields and select 'Yes' for at least one checklist item.")

LOG_FILE = "user_log.csv"

def log_user_data(user_data):
    log_entry = {
        "Timestamp": user_data["timestamp"],
        "Username": user_data["username"],
        "Bench No": user_data["bench_no"],
        "LSD": user_data["lsd"],
        "Base": user_data["base"],
        "Matrix": user_data["matrix"],
        "Model": user_data["model"],
        "Stabilization": user_data["checklist"]["stabilization"],
        "Maintenance": user_data["checklist"]["maintenance"],
        "Diagnostics": user_data["checklist"]["Diagnostics"],
        "Preparation": user_data["checklist"]["preparation"]
    }

    df_log = pd.DataFrame([log_entry])
    if not os.path.exists(LOG_FILE):
        df_log.to_csv(LOG_FILE, index=False)
    else:
        df_log.to_csv(LOG_FILE, mode='a', index=False, header=False)

if os.path.exists(LOG_FILE):
    st.markdown("### 👥 Download User Activity Log")
    with open(LOG_FILE, "rb") as f:
        st.download_button(
            label="📥 Download Log (CSV)",
            data=f,
            file_name="APS_user_log.csv",
            mime="text/csv"
        )
