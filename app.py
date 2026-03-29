import streamlit as st
import sqlite3
import pandas as pd

# Connect DB
def get_connection():
    return sqlite3.connect("data/inspections.db")

st.title("🐾 USDA Animal Welfare Violations Dashboard")

conn = get_connection()

# Sidebar
st.sidebar.header("Filters")
option = st.sidebar.selectbox(
    "Select Query",
    ["Critical Violations", "Repeat Violations", "Species Filter"]
)

# 🔥 Critical Violations
if option == "Critical Violations":
    st.subheader("🚨 Critical Violations")

    query = """
        SELECT DISTINCT f.name, f.location, v.date, v.severity
        FROM violations v
        JOIN facilities f ON v.facility_id = f.id
        WHERE LOWER(v.severity) LIKE '%critical%'
    """

    df = pd.read_sql_query(query, conn)
    st.dataframe(df)

# 🔁 Repeat Violations
elif option == "Repeat Violations":
    st.subheader("🔁 Repeat Violations")

    query = """
        SELECT f.name, COUNT(*) as count
        FROM violations v
        JOIN facilities f ON v.facility_id = f.id
        GROUP BY f.name
        HAVING count > 1
        ORDER BY count DESC
    """

    df = pd.read_sql_query(query, conn)
    st.dataframe(df)

# 🐾 Species Filter
elif option == "Species Filter":
    st.subheader("🐾 Filter by Species")

    species = st.text_input("Enter species (e.g., deer, cattle, goat)")

    if species:
        query = """
            SELECT f.name, v.date, v.severity, v.species
            FROM violations v
            JOIN facilities f ON v.facility_id = f.id
            WHERE LOWER(v.species) LIKE ?
            OR LOWER(v.notes) LIKE ?
        """

        df = pd.read_sql_query(query, conn, params=(f"%{species.lower()}%", f"%{species.lower()}%"))
        st.dataframe(df)