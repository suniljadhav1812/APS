# pages/1_Accuracy_and_Precision.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from difflib import get_close_matches
import io

TEMP_FILE = "temp_user_data.json"

st.set_page_config(page_title="Accuracy and Precision", layout="wide")
st.title("🧪 Accuracy & Precision Test")

# Load user session
def load_user_data():
    try:
        with open(TEMP_FILE, "r") as f:
            return json.load(f)
    except:
        st.error("User data not found. Please complete the main form first.")
        st.stop()

user_data = load_user_data()
base = user_data.get("base", "")
matrix = user_data.get("matrix", "")
samples = []

# Load expected samples
try:
    xls = pd.read_excel("Precision_tables/Database_base_matrix.xlsx", sheet_name=None)
    if base in xls and matrix in xls[base].columns:
        samples = xls[base][matrix].dropna().tolist()
except Exception as e:
    st.error(f"Error loading base/matrix sample data: {e}")
    st.stop()

sample_count = len(samples)
st.info(f"🧾 Expected Samples: {sample_count}")

# Upload Excel report
uploaded_file = st.file_uploader("📤 Upload Excel Report", type=["xlsx", "xls"])

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file, header=None)
    st.success("Excel file uploaded successfully.")
    
    sample_blocks = []
    i = 0
    found_samples = 0

    while i < len(df_raw):
        row = df_raw.iloc[i]
        if isinstance(row[0], str) and "Sample Name" in row[0]:
            found_samples += 1
            parts = row[0].split("|")
            sample_name = next((p.split(":")[1].strip() for p in parts if "sample name" in p.lower()), f"Sample_{found_samples}")

            i += 1
            headers = df_raw.iloc[i].tolist()
            i += 1

            block_data = []
            while i < len(df_raw) and not df_raw.iloc[i].isnull().all():
                block_data.append(df_raw.iloc[i].tolist())
                i += 1

            df_sample = pd.DataFrame(block_data, columns=headers)
            df_sample["Sample Name"] = sample_name
            sample_blocks.append(df_sample)
        else:
            i += 1

    if found_samples != sample_count:
        st.warning(f"Expected {sample_count} samples, but found {found_samples} samples.")

    if not sample_blocks:
        st.error("No valid sample data found in uploaded file.")
        st.stop()

    final_df = pd.concat(sample_blocks, ignore_index=True)

    # Sample name mapping
    expected_samples = [str(s).strip().upper() for s in samples]
    final_df["Sample Name"] = final_df["Sample Name"].astype(str).str.strip().str.upper()
    imported_samples = final_df["Sample Name"].unique().tolist()

    # Auto map or suggest
    mapping = {}
    manual_mapping_needed = {}
    
    for expected in expected_samples:
        match = get_close_matches(expected, imported_samples, n=1, cutoff=0.9)
        if match:
            mapping[match[0]] = expected  # reverse: imported → expected
        else:
            manual_mapping_needed[expected] = None
    
    # Ask for manual mapping if needed
    if manual_mapping_needed:
        st.warning("🔧 Some samples couldn't be auto-mapped. Please map them manually.")
    
        for expected in manual_mapping_needed:
            selected = st.selectbox(
                f"Map expected sample '{expected}' to:",
                options=["❌ Not Found"] + imported_samples,
                key=f"map_{expected}"
            )
            if selected != "❌ Not Found":
                mapping[selected] = expected  # Add to mapping
    
    # Apply mapping to final_df
    final_df["Sample Name"] = final_df["Sample Name"].replace(mapping)
    
    # Display mapping table
    df_mapping = pd.DataFrame({
        "Expected Sample": expected_samples,
        "Imported Sample": [next((k for k, v in mapping.items() if v == e), "❌ Not Found") for e in expected_samples]
    })
    st.subheader("🔗 Sample Mapping")
    st.dataframe(df_mapping)


    # Update names in final_df
    final_df["Sample Name"] = final_df["Sample Name"].replace(mapping)

    # Clean and compute
    final_df["Elements"] = final_df["Elements"].str.replace(" (%)", "", regex=False).str.strip().str.capitalize()
    base_name = base.strip().capitalize()
    final_df = final_df[final_df["Elements"] != base_name]

    # Remove outliers / placeholders
    final_df = final_df[~final_df["Mean"].astype(str).str.contains("<|>")]
    final_df["CV"] = final_df.apply(lambda row: row["Mean"] if str(row["Cert. Val."]).strip() == '-' else row["Cert. Val."], axis=1)
    final_df["SD"] = pd.to_numeric(final_df["SD"], errors="coerce").fillna(0)
    final_df["CertValNum"] = pd.to_numeric(final_df["Cert. Val."], errors="coerce")
    final_df["DEV"] = (final_df["CertValNum"] - final_df["Mean"]).abs()

    # Calculate Limits — Placeholder logic (to be updated based on precision matrix)
    # Merge Acceptance columns if exact column not found
    final_df["Acceptance"] = np.nan
    for col in final_df.columns:
        if col.startswith("Acceptance"):
            temp = pd.to_numeric(final_df[col].replace("-", np.nan), errors="coerce")
            if "2s" in col:
                temp = temp / 2
            elif "3s" in col:
                temp = temp / 3
            final_df["Acceptance"] = final_df["Acceptance"].combine_first(temp)
    
    final_df["A_Limit"] = pd.to_numeric(final_df["Acceptance"], errors="coerce")
    final_df["P_Limit"] = final_df["CV"].astype(float) * 0.05  # ← update with real lookup

    # Accuracy and Precision
    final_df["A_Result"] = final_df.apply(
        lambda row: "Pass" if pd.notna(row["DEV"]) and pd.notna(row["A_Limit"]) and row["DEV"] <= row["A_Limit"] else "Fail",
        axis=1
    )

    final_df["P_Result"] = final_df.apply(
        lambda row: "Pass" if pd.notna(row["SD"]) and pd.notna(row["P_Limit"]) and row["SD"] <= row["P_Limit"] else "Fail",
        axis=1
    )

    final_df["%DEV_A"] = ((final_df["DEV"] / final_df["A_Limit"]) * 100).round(2)
    final_df["%DEV_P"] = ((final_df["SD"] / final_df["P_Limit"]) * 100).round(2)

    st.subheader("📊 Summary Results")

    # Filter out rows with NaN in %DEV_A and %DEV_P
    valid_accuracy = final_df[final_df["%DEV_A"].notna()]
    valid_precision = final_df[final_df["%DEV_P"].notna()]
    
    # Count only valid and "Pass" entries
    accuracy_pass_count = valid_accuracy[valid_accuracy["A_Result"] == "Pass"].shape[0]
    precision_pass_count = valid_precision[valid_precision["P_Result"] == "Pass"].shape[0]
    
    # Total valid counts
    accuracy_total = valid_accuracy.shape[0]
    precision_total = valid_precision.shape[0]
    
    # Show metrics
    colA1, colA2 = st.columns(2)
    with colA1:
        st.metric("Accuracy Pass", f"{accuracy_pass_count} / {accuracy_total}")
    with colA2:
        st.metric("Precision Pass", f"{precision_pass_count} / {precision_total}")


    st.dataframe(final_df[["Sample Name", "Elements", "Mean", "Cert. Val.", "DEV", "A_Limit", "%DEV_A", "A_Result", "SD", "P_Limit", "%DEV_P", "P_Result"]])

    with st.expander("📥 Download Final Result as Excel"):
        

        # Create a BytesIO buffer
        buffer = io.BytesIO()
        
        # Write the DataFrame to the buffer
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False)
        
        # Rewind the buffer
        buffer.seek(0)
        
        # Show the download button
        st.download_button(
            label="Download .xlsx",
            data=buffer,
            file_name="APS_AccuracyPrecision_Result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )




## ✅ Folder Structure Reminder

