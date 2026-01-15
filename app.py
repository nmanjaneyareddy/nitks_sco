import streamlit as st
import pandas as pd
import re
from io import BytesIO

# -------------------------------------------------
# Page configuration
# -------------------------------------------------
st.set_page_config(
    page_title="NITK Publication Affiliation Analyzer",
    layout="wide"
)

st.title("📚 NITK Publication Affiliation Analyzer")
st.markdown(
    "Upload **Excel (.xls / .xlsx) or CSV** files to extract "
    "**NITK affiliations** with **publication count and total citations**."
)

# -------------------------------------------------
# File upload
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload Excel or CSV file",
    type=["csv", "xls", "xlsx"]
)

if uploaded_file:
    file_name = uploaded_file.name.lower()

    # ---------- Read file ----------
    if file_name.endswith(".csv"):
        try:
            df = pd.read_csv(uploaded_file)
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding="latin1")
    elif file_name.endswith(".xls"):
        df = pd.read_excel(uploaded_file, engine="xlrd")
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

    st.success("File uploaded successfully")

    st.write("### 🔍 Data Preview")
    st.dataframe(df.head())

    # -------------------------------------------------
    # Column selection
    # -------------------------------------------------
    st.write("## ⚙️ Column Mapping")

    affiliations_col = st.selectbox("Affiliations column", df.columns)
    year_column = st.selectbox("Year column", df.columns)
    cited_by_column = st.selectbox("Cited by column", df.columns)

    # -------------------------------------------------
    # Extract NITK affiliation
    # -------------------------------------------------
    def extract_nitk_affiliation(text):
        if pd.isna(text):
            return None
        parts = re.split(r";\s*", str(text))
        for part in parts:
            if re.search(
                r"National Institute of Technology Karnataka",
                part,
                re.IGNORECASE,
            ):
                return part.strip()
        return None

    df["NITK_Affiliation"] = df[affiliations_col].apply(
        extract_nitk_affiliation
    )

    # -------------------------------------------------
    # Normalize Year
    # -------------------------------------------------
    df[year_column] = (
        df[year_column]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .fillna("Unknown")
    )

    # -------------------------------------------------
    # Clean Cited by column
    # -------------------------------------------------
    df[cited_by_column] = (
        df[cited_by_column]
        .astype(str)
        .str.extract(r"(\d+)")[0]
        .fillna(0)
        .astype(int)
    )

    # -------------------------------------------------
    # Affiliation category
    # -------------------------------------------------
    def label_affiliation(row):
        if pd.isna(row[affiliations_col]):
            return "Blank Affiliation"
        elif pd.notna(row["NITK_Affiliation"]):
            return row["NITK_Affiliation"]
        else:
            return "No NITK Mention"

    df["Affiliation_Category"] = df.apply(
        label_affiliation, axis=1
    )

    # -------------------------------------------------
    # Year-wise affiliation counts + citation sum
    # -------------------------------------------------
    yearwise_stats = (
        df.groupby([year_column, "Affiliation_Category"])
        .agg(
            Count=("Affiliation_Category", "size"),
            Total_Cited_By=(cited_by_column, "sum"),
        )
        .reset_index()
        .sort_values(
            by=[year_column, "Count"],
            ascending=[True, False]
        )
    )

    # -------------------------------------------------
    # Total (all years)
    # -------------------------------------------------
    total_stats = (
        df.groupby("Affiliation_Category")
        .agg(
            Count=("Affiliation_Category", "size"),
            Total_Cited_By=(cited_by_column, "sum"),
        )
        .reset_index()
        .sort_values(by="Count", ascending=False)
    )

    total_stats.insert(0, year_column, "Total")

    combined_stats = pd.concat(
        [yearwise_stats, total_stats],
        ignore_index=True
    )

    st.write("## 📊 Year-wise & Total Affiliation Statistics")
    st.dataframe(combined_stats)

    # -------------------------------------------------
    # NITK-only publications
    # -------------------------------------------------
    nitk_only = df[df["NITK_Affiliation"].notna()]

    st.write("## 🧹 NITK-Dept-wise Publications")
    st.dataframe(nitk_only.head())

    # -------------------------------------------------
    # Excel download helper
    # -------------------------------------------------
    def to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False)
        return output.getvalue()

    # -------------------------------------------------
    # Downloads
    # -------------------------------------------------
    st.write("## ⬇️ Download Reports")

    st.download_button(
        "Download Affiliation Statistics",
        data=to_excel(combined_stats),
        file_name="NITK_Affiliation_Counts_with_Citations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.download_button(
        "Download NITK-Dept-wise Publications",
        data=to_excel(nitk_only),
        file_name="NITK_Dept-wise_Publications.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
