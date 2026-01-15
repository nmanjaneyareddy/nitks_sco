import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="NITK Publication Analyzer", layout="wide")

st.title("📚 NITK Publication Affiliation Analyzer")

st.markdown("""
Upload an Excel file containing **Affiliations** and **Year** columns.
The app will extract NITK affiliations and generate year-wise statistics.
""")

# -----------------------------
# Upload file
# -----------------------------
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")
    st.write("### Dataset Preview")
    st.dataframe(df.head())

    # -----------------------------
    # Column selection
    # -----------------------------
    affiliations_col = st.selectbox(
        "Select Affiliations column",
        df.columns,
        index=df.columns.get_loc("Affiliations") if "Affiliations" in df.columns else 0
    )

    year_column = st.selectbox(
        "Select Year column",
        df.columns,
        index=df.columns.get_loc("Year") if "Year" in df.columns else 0
    )

    # -----------------------------
    # Extract NITK affiliation
    # -----------------------------
    def extract_nitk_affiliation(text):
        if pd.isna(text):
            return None
        parts = re.split(r';\s*', str(text))
        for part in parts:
            if re.search(r'National Institute of Technology Karnataka', part, re.IGNORECASE):
                return part.strip()
        return None

    df["NITK_Affiliation"] = df[affiliations_col].apply(extract_nitk_affiliation)

    # -----------------------------
    # Normalize Year
    # -----------------------------
    df[year_column] = (
        df[year_column]
        .astype(str)
        .str.extract(r'(\d{4})')[0]
        .fillna("Unknown")
    )

    # -----------------------------
    # Affiliation category
    # -----------------------------
    def label_affiliation(row):
        if pd.isna(row[affiliations_col]):
            return "Blank Affiliation"
        elif pd.notna(row["NITK_Affiliation"]):
            return row["NITK_Affiliation"]
        else:
            return "No NITK Mention"

    df["Affiliation_Category"] = df.apply(label_affiliation, axis=1)

    # -----------------------------
    # Year-wise counts
    # -----------------------------
    yearwise_counts = (
        df.groupby([year_column, "Affiliation_Category"])
        .size()
        .reset_index(name="Count")
        .sort_values(by=[year_column, "Count"], ascending=[True, False])
    )

    # -----------------------------
    # Total counts
    # -----------------------------
    total_counts = (
        df.groupby("Affiliation_Category")
        .size()
        .reset_index(name="Count")
        .sort_values(by="Count", ascending=False)
    )
    total_counts.insert(0, year_column, "Total")

    combined = pd.concat([yearwise_counts, total_counts], ignore_index=True)

    # -----------------------------
    # Display results
    # -----------------------------
    st.write("### 📊 Year-wise & Total Affiliation Counts")
    st.dataframe(combined)

    # -----------------------------
    # Download Excel
    # -----------------------------
    def to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        label="⬇️ Download Affiliation Counts Excel",
        data=to_excel(combined),
        file_name="NITK_affiliation_counts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # -----------------------------
    # Filtered NITK-only data
    # -----------------------------
    nitk_only = df[df["NITK_Affiliation"].notna()]

    st.write("### 🧹 NITK-only Publications")
    st.dataframe(nitk_only.head())

    st.download_button(
        label="⬇️ Download NITK-only Publications",
        data=to_excel(nitk_only),
        file_name="NITK_only_publications.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
