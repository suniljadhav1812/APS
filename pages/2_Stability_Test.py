import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from io import BytesIO
from datetime import datetime
import io

st.set_page_config(page_title="Stability Test", layout="wide")
st.title("📈 Stability Test (Short / Long Term)")

TEMP_FILE = "temp_user_data.json"

# Check if the file exists
if not os.path.exists(TEMP_FILE):
    st.warning("⚠️ Please fill out the main form before starting the Stability Test.")
    st.stop()

# Read the data
with open(TEMP_FILE, "r") as f:
    user_data = json.load(f)

# Optional: Check if important values are present
required = ["username", "bench_no", "lsd"]
if not all(k in user_data for k in required):
    st.warning("⚠️ Missing information. Please re-fill the main form.")
    st.stop()


# Load saved user data
@st.cache_data
def load_user_data():
    if not os.path.exists(TEMP_FILE):
        return None
    try:
        with open(TEMP_FILE, "r") as f:
            return json.load(f)
    except:
        return None

user_data = load_user_data()

if not user_data:
    st.warning("⚠️ Please fill out the main form before starting the Stability Test.")
    st.stop()

def load_precision_table(model_name, base_name):
    folder = "Precision_tables"
    model_parts = model_name.split()
    if len(model_parts) < 2:
        return None
    raw_model_code = model_parts[1]
    core_model_code = raw_model_code.split("_")[0]

    for file in os.listdir(folder):
        if file.startswith("Precision_figures") and core_model_code in file and file.endswith(".xlsx"):
            df = pd.read_excel(os.path.join(folder, file), sheet_name=base_name, skiprows=[1])
            df.columns = df.columns.str.strip()
            df.iloc[:, 0] = pd.to_numeric(df.iloc[:, 0], errors='coerce')
            return df
    return None

def lookup_threshold(cert_val, element, df_table):
    try:
        cert_val = float(cert_val)
    except:
        return None
    col = element.strip()
    filtered = df_table[df_table[df_table.columns[0]] >= cert_val]
    if not filtered.empty and col in df_table.columns:
        return filtered.iloc[0][col]
    return None

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
    df_raw = pd.read_excel(uploaded_file, header=None)
    st.success("Stability report loaded.")

    precision_df = load_precision_table(model, base)
    if precision_df is None:
        st.error("Matching precision threshold file not found.")
        st.stop()

    blocks = []
    i = 0
    while i < len(df_raw):
        row = df_raw.iloc[i]
        if isinstance(row[0], str) and "Sample Name" in row[0]:
            parts = row[0].split("|")
            sample_o = parts[3].split(":")[1].strip()
            matrix_o = parts[1].split(":")[1].strip()

            i += 1
            headers = df_raw.iloc[i].tolist()
            i += 1
            data = []
            while i < len(df_raw) and not df_raw.iloc[i].isnull().all():
                data.append(df_raw.iloc[i].tolist())
                i += 1
            df_block = pd.DataFrame(data, columns=headers)
            df_block["Elements"] = df_block["Elements"].str.replace(" (%)", "", regex=False).str.strip().str.capitalize()

            # Clean
            df_block = df_block[~df_block["Mean"].astype(str).str.contains("<|>")]
            df_block["CV"] = df_block.apply(lambda row: row["Mean"] if row["Cert. Val."] == '-' else row["Cert. Val."], axis=1)
            df_block["SD"] = pd.to_numeric(df_block["SD"], errors="coerce").fillna(0)
            df_block["CertValNum"] = pd.to_numeric(df_block["Cert. Val."], errors="coerce")
            df_block["DEV"] = (df_block["CertValNum"] - df_block["Mean"]).abs()

            # Merge Acceptance
            df_block["Acceptance"] = np.nan
            for col in [c for c in df_block.columns if c.startswith("Acceptance")]:
                temp = pd.to_numeric(df_block[col].replace("-", np.nan), errors="coerce")
                if "2s" in col:
                    temp = temp / 2
                elif "3s" in col:
                    temp = temp / 3
                df_block["Acceptance"] = df_block["Acceptance"].combine_first(temp)
            df_block["S_Limit"] = pd.to_numeric(df_block["Acceptance"], errors="coerce")

            set_number = len(blocks) + 1
            df_block.insert(0, "Set", f"{set_number}")
            blocks.append(df_block)
        else:
            i += 1

    expected_sets = 8 if st.session_state.stab_type == "ShortTerm" else 16
    if len(blocks) != expected_sets:
        st.error(f"{st.session_state.stab_type} Stability requires exactly {expected_sets} sets. Found {len(blocks)}.")
        st.stop()

    final_df = pd.concat(blocks, ignore_index=True)
    base_name = base.strip().capitalize()
    final_df = final_df[final_df["Elements"].str.capitalize() != base_name]

    final_df["CV"] = pd.to_numeric(final_df["CV"], errors="coerce")
    final_df["S_Limit0"] = final_df.apply(lambda row: lookup_threshold(row["CV"], row["Elements"], precision_df), axis=1)
    final_df["S_Limit"] = np.where(final_df["S_Limit"].isna(), final_df["S_Limit0"], final_df["S_Limit"])

    # Excluded Elements
    excluded_elements = []
    with open("Precision_tables/Exluded_Elements.txt", "r") as file:
        excluded_elements = [e.strip().upper() for e in file.read().split(",") if e.strip()]

    # Apply multiplier
    multiplier = 1.5 if st.session_state.stab_type == "ShortTerm" else 3
    final_df["Elements"] = final_df["Elements"].str.upper()
    final_df["S_Limit"] = final_df.apply(
        lambda row: row["S_Limit"] * 3 if row["Elements"] in excluded_elements else row["S_Limit"] * multiplier,
        axis=1
    )

    final_df["%DEV_S"] = final_df.apply(
        lambda row: round((row["DEV"] / row["S_Limit"]) * 100, 2) if pd.notna(row["DEV"]) and pd.notna(row["S_Limit"]) else None,
        axis=1
    )

    final_df["S_Result"] = final_df.apply(
        lambda row: "Pass" if pd.notna(row["DEV"]) and row["DEV"] <= row["S_Limit"] else "Fail"
        if pd.notna(row["DEV"]) else "NA",
        axis=1
    )

    # Group Summary
    def summarize_stability(group):
        if (group["Cert. Val."] == "-").all():
            return "NA"
        return "Pass" if (group["S_Result"] == "Pass").all() else "Fail"

    filtered_df = final_df[~final_df['Cert. Val.'].astype(str).str.contains("-", na=False)]
    element_summary = filtered_df.groupby("Elements").apply(summarize_stability).reset_index()
    element_summary.columns = ["Elements", "Stability_Result"]
    element_summary["Elements"] = element_summary["Elements"].str.title()
    final_df["Elements"] = final_df["Elements"].str.capitalize()
    st.subheader("📋 Stability Result Summary")
    stability_pass_count = element_summary[element_summary["Stability_Result"] == "Pass"].shape[0]
    stability_total = element_summary[element_summary["Stability_Result"].isin(["Pass", "Fail"])].shape[0]
    

    colS1, _ = st.columns(2)
    with colS1:
        st.metric("Stability Pass", f"{stability_pass_count} / {stability_total}")
    
    # Show Stability result table
    st.dataframe(element_summary)

    # Show full results with option to download
    st.subheader("📋 Stability Summary Table")
    st.dataframe(final_df[[
    "Set", "Elements", "Mean", "Cert. Val.", 
    "DEV", "S_Limit", "%DEV_S", "S_Result" 
]])

    
    # Step 1: Create the in-memory buffer
    buffer = io.BytesIO()
    
    # Step 2: Write the DataFrame to Excel using openpyxl
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        final_df.to_excel(writer, index=False)
    
    # Step 3: Rewind the buffer to the beginning
    buffer.seek(0)
    
    # Step 4: Create download button
    st.download_button(
        label="Download .xlsx",
        data=buffer,
        file_name="APS_AccuracyPrecision_Result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

