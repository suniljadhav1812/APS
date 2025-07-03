
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

st.set_page_config(page_title="APS Tool", layout="wide")

st.title("APS Tool (Web Version)")

with st.sidebar:
    st.header("User Info")
    username = st.text_input("Name")
    bench_no = st.text_input("Bench No")
    lsd = st.date_input("Last Standardization Date", max_value=datetime.today())

    st.header("Checklist")
    stab = st.checkbox("Stabilization")
    maint = st.checkbox("Routine Maintenance")
    err_free = st.checkbox("Error Free")
    prep = st.checkbox("Sample Preparation")

st.markdown("## Step 1: Select Metadata")
# Load base and matrix from Excel
base_file = "Precision_tables/Database_base_matrix.xlsx"
matrix = ""
if os.path.exists(base_file):
    base_data = pd.read_excel(base_file, sheet_name=None)
    base = st.selectbox("Base", list(base_data.keys()))
    matrix = st.selectbox("Matrix", base_data[base].columns.tolist())
else:
    st.error("Base/Matrix Excel not found.")

st.markdown("## Step 2: Upload Report File")
uploaded = st.file_uploader("Upload your report Excel file", type=["xlsx", "xls"])

if uploaded:
    df = pd.read_excel(uploaded, header=None)
    st.success("File uploaded successfully!")
    st.write("First few rows of data:")
    st.dataframe(df.head())

    # Optionally, save the uploaded file
    with open("uploaded_file.xlsx", "wb") as f:
        f.write(uploaded.getbuffer())

    st.markdown("### ✔️ Ready to process further...")
else:
    st.info("Please upload an Excel report to proceed.")
