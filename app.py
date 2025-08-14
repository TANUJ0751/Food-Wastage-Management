# app.py
from streamlit_option_menu import option_menu
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# === DB Connection ===
DB_NAME = "food_wastage.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

# === Helper: Run SQL Query ===
def run_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# === Title ===
st.set_page_config(page_title="Local Food Wastage Management System", layout="wide")
st.title(" Local Food Wastage Management System")

menu=option_menu(
    menu_title=None,  # No title
    options=["Dashboard", "Add Food Listing", "Update Listing", "Delete Listing", "SQL Insights"],
    icons=["speedometer", "plus-circle", "pencil", "trash", "bar-chart"],  # optional icons
    menu_icon="cast",
    default_index=0,
    orientation="horizontal"
)
# === 1. Dashboard ===
if menu == "Dashboard":
    st.subheader("📊 Food Listings Overview")
    query = "SELECT * FROM food_listings"
    df = run_query(query)

    city_filter = st.selectbox("Filter by City", ["All"] + list(df["Location"].unique()))
    if city_filter != "All":
        df = df[df["Location"] == city_filter]

    st.dataframe(df)

# === 2. Add Food Listing ===
elif menu == "Add Food Listing":
    st.subheader("➕ Add New Food Listing")
    with st.form("add_food"):
        food_name = st.text_input("Food Name")
        quantity = st.number_input("Quantity", min_value=1)
        expiry = st.date_input("Expiry Date")
        provider_id = st.number_input("Provider ID", min_value=1)
        provider_type = st.text_input("Provider Type")
        location = st.text_input("Location")
        food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
        submitted = st.form_submit_button("Add Listing")

    if submitted:
        conn = get_connection()
        conn.execute("""
            INSERT INTO food_listings (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (food_name, quantity, expiry, provider_id, provider_type, location, food_type, meal_type))
        conn.commit()
        conn.close()
        st.success("✅ Food listing added successfully!")

# === 3. Update Listing ===
elif menu == "Update Listing":
    st.subheader("✏️ Update Food Listing")
    listings = run_query("SELECT Food_ID, Food_Name FROM food_listings")
    listing_id = st.selectbox("Select Food ID", listings["Food_ID"])

    if listing_id:
        new_qty = st.number_input("New Quantity", min_value=1)
        if st.button("Update Quantity"):
            conn = get_connection()
            conn.execute("UPDATE food_listings SET Quantity = ? WHERE Food_ID = ?", (new_qty, listing_id))
            conn.commit()
            conn.close()
            st.success("✅ Quantity updated successfully!")

# === 4. Delete Listing ===
elif menu == "Delete Listing":
    st.subheader("🗑️ Delete Food Listing")
    listings = run_query("SELECT Food_ID, Food_Name FROM food_listings")
    listing_id = st.selectbox("Select Food ID to Delete", listings["Food_ID"])

    if st.button("Delete Listing"):
        conn = get_connection()
        conn.execute("DELETE FROM food_listings WHERE Food_ID = ?", (listing_id,))
        conn.commit()
        conn.close()
        st.success("✅ Listing deleted successfully!")

# === 5. SQL Insights ===
elif menu == "SQL Insights":
    st.subheader(" Data Insights-15 Key Queries")

    queries = {
        # 1
        "1️ Providers & Receivers Count by City":
            """
            SELECT City, 
                   (SELECT COUNT(*) FROM providers p WHERE p.City = c.City) AS Providers,
                   (SELECT COUNT(*) FROM receivers r WHERE r.City = c.City) AS Receivers
            FROM (SELECT DISTINCT City FROM providers
                  UNION
                  SELECT DISTINCT City FROM receivers) c
            """,

        # 2
        "2️ Top Food Provider Types":
            """
            SELECT Type, COUNT(*) AS Count
            FROM providers
            GROUP BY Type
            ORDER BY Count DESC
            """,

        # 3
        "3️ Contact Info of Providers by City":
            """
            SELECT Name, Type, Contact
            FROM providers
            WHERE City = 'Mumbai'
            """,  # You can make city dynamic with st.selectbox

        # 4
        "4️ Receivers with Most Claims":
            """
            SELECT r.Name, COUNT(c.Claim_ID) AS Total_Claims
            FROM claims c
            JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
            GROUP BY r.Name
            ORDER BY Total_Claims DESC
            """,

        # 5
        "5️ Total Quantity of Food Available":
            "SELECT SUM(Quantity) AS Total_Quantity FROM food_listings",

        # 6
        "6️ City with Highest Number of Food Listings":
            """
            SELECT Location, COUNT(*) AS Listings_Count
            FROM food_listings
            GROUP BY Location
            ORDER BY Listings_Count DESC
            LIMIT 1
            """,

        # 7
        "7️ Most Common Food Types":
            """
            SELECT Food_Type, COUNT(*) AS Count
            FROM food_listings
            GROUP BY Food_Type
            ORDER BY Count DESC
            """,

        # 8
        "8️ Food Claims Count per Food Item":
            """
            SELECT f.Food_Name, COUNT(c.Claim_ID) AS Claims_Count
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            GROUP BY f.Food_Name
            """,

        # 9
        "9️ Provider with Most Successful Claims":
            """
            SELECT p.Name, COUNT(c.Claim_ID) AS Successful_Claims
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            WHERE c.Status = 'Completed'
            GROUP BY p.Name
            ORDER BY Successful_Claims DESC
            LIMIT 1
            """,

        # 10
        "10  Claims Status Percentage":
            """
            SELECT Status,
                   ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims)), 2) AS Percentage
            FROM claims
            GROUP BY Status
            """,

        # 11
        "1️1️ Average Quantity Claimed per Receiver":
            """
            SELECT r.Name, AVG(f.Quantity) AS Avg_Quantity_Claimed
            FROM claims c
            JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            GROUP BY r.Name
            """,

        # 12
        "1️2️ Most Claimed Meal Type":
            """
            SELECT f.Meal_Type, COUNT(c.Claim_ID) AS Claims_Count
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            GROUP BY f.Meal_Type
            ORDER BY Claims_Count DESC
            """,

        # 13
        "1️3️ Total Quantity Donated by Each Provider":
            """
            SELECT p.Name, SUM(f.Quantity) AS Total_Quantity
            FROM food_listings f
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Name
            ORDER BY Total_Quantity DESC
            """,

        # 14
        "1️4 Highest Demand Location (Most Claims)":
            """
            SELECT f.Location, COUNT(c.Claim_ID) AS Claims_Count
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            GROUP BY f.Location
            ORDER BY Claims_Count DESC
            LIMIT 1
            """,

        # 15
        "1️5️ Provider Contribution Summary":
            """
            SELECT p.Name, p.Type, COUNT(f.Food_ID) AS Total_Items, SUM(f.Quantity) AS Total_Quantity
            FROM food_listings f
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Name, p.Type
            ORDER BY Total_Quantity DESC
            """
    }

    selected_key = st.selectbox("Choose an option:",options=list(queries.keys()))

    if selected_key=="3️ Contact Info of Providers by City":
        cities=run_query("SELECT * FROM food_listings")
        selected_city=st.selectbox("Filter by City",list(cities["Location"].unique()))
        queries[selected_key]= f"SELECT Name, Type, Contact FROM providers WHERE City = '{selected_city}'"
    st.markdown(f"### {selected_key}")
    df = run_query(queries[selected_key])
    st.dataframe(df)
