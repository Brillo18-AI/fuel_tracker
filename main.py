import streamlit as st
from datetime import datetime
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
st.cache_data.clear()

# Page config
st.set_page_config(page_title="Fuel Tracker", layout="wide")

# Custom formatting for manager input
def formatted_number_input(label, key, default=0):
    raw = st.text_input(label, value=str(default), key=key)
    try:
        value = int(raw.replace(",", "").strip())
        st.caption(f"↳ {value:,} liters")  # This shows the formatted value below the input
        return value
    except ValueError:
        st.warning("Please enter a valid number")
        return 0




# Function to enable mobile zoom and add zoom slider
def apply_zoom():
    # Viewport meta for pinch-zoom support
    st.markdown(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0, user-scalable=yes">',
        unsafe_allow_html=True
    )
    # Sidebar slider to adjust zoom percentage
    zoom = st.slider("Page Zoom (%)", min_value=50, max_value=110, value=100)
    # Inject CSS for zoom
    st.markdown(
        f"""
        <style>
            html, body, .stApp, .stDataFrame, .stTable {{
                zoom: {zoom}% !important;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


# Google Sheets helper
def connect_to_sheet():
    try:
        creds_info = st.secrets["google_service_account"]
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open("FuelTracker")
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

# Authentication sidebar

def login():
    st.sidebar.title("BINAC OIL LIMITED FUEL TRACKER")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        sheet = connect_to_sheet()
        if sheet:
            users = sheet.worksheet("users").get_all_records()
            for u in users:
                if u['username'].strip().lower() == username.strip().lower() and u['password'].strip() == password.strip():
                    st.session_state.user = u
                    st.rerun()
            st.sidebar.error("Invalid credentials")


# Manager view with inputs with pump features
def manager_view(station_id):
    st.title("Daily Pump Report")

    st.markdown(f"### Station: **{station_id}**")
    date = st.date_input("Date", datetime.now())

    tanks = ["Tank 1", "Tank 2", "Tank 3", "Tank 4"]
    pumps = ["Pump A", "Pump B", "Pump C", "Pump D"]

    selected_tank = st.selectbox("Select Tank", tanks)
    selected_pump = st.selectbox("Select Pump", pumps)

    price_per_liter = st.number_input("Price per Liter (₦)", min_value=0.0, format="%.2f")

    open_meter = st.number_input("Open Meter Reading", min_value=0.0, format="%.2f")
    close_meter = st.number_input("Close Meter Reading", min_value=open_meter, format="%.2f")

    expected_liters = st.number_input("Expected Liters (or auto-calc)", value=close_meter - open_meter, format="%.2f")
    expected_cash = st.number_input("Expected Cash (₦)", value=expected_liters * price_per_liter, format="%.2f")

    expenses = st.number_input("Expenses (₦)", min_value=0.0, format="%.2f")
    cash_at_hand = st.number_input("Cash at Hand (₦)", min_value=0.0, format="%.2f")

    if st.button("Submit Report"):
        sheet = connect_to_sheet()
        if sheet:
            try:
                ws = sheet.worksheet("pump_reports")
                ws.append_row([
                    date.strftime("%Y-%m-%d"),
                    station_id,
                    selected_tank,
                    selected_pump,
                    price_per_liter,
                    open_meter,
                    close_meter,
                    expected_liters,
                    expected_cash,
                    expenses,
                    cash_at_hand
                ])
                st.success("Pump report submitted successfully!")
            except Exception as e:
                st.error(f"Failed to save report: {e}")
        else:
            st.error("Google Sheet connection failed.")


# Owner view (with zoom control)
def owner_view():
    st.title("All Stations Dashboard")
    sheet = connect_to_sheet()
    if sheet:
        records = sheet.worksheet("daily_reports").get_all_records()
        df = pd.DataFrame(records)
        
        df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
        from_date = st.date_input("From date", datetime.now())
        df = df[df['date'] >= pd.to_datetime(from_date)]
        
        # Get unique stations and allow owner to select one
        stations = df['station_id'].unique()
        station_selected = st.selectbox("Select a station", stations)

        # Filter only the selected station
        station_df = df[df['station_id'] == station_selected]

        
        tanks = station_df['tank_no'].unique()
        for tank in tanks:
            st.markdown(f" {tank}")
            tank_df = station_df[station_df['tank_no'] == tank]
            # Initialize display_df with required columns
            display_df = tank_df[['date', 'opening', 'received', 'sales', 'closing', 'balance', 'revenue', 'price per liter']].copy()

            # Format 'price per liter' with ₦ symbol
            if 'price per liter' in display_df.columns:
                display_df['price per liter'] = display_df['price per liter'].apply(lambda x: f"₦{x:,.2f}" if isinstance(x, (int, float)) else x)
            
            # Format 'revenue' with ₦ symbol
            display_df['revenue'] = display_df['revenue'].apply(lambda x: f"₦{x:,.2f}" if isinstance(x, (int, float)) else x)




            # Format numeric columns with comma separation
            for col in ['opening', 'received', 'sales', 'closing', 'balance']:
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)

            # display dataframe
            st.dataframe(
                display_df.sort_values('date').reset_index(drop=True)
            )
            


            st.write("---")
    else:
        st.error("Couldn't load data.")
        
    apply_zoom()
# Main flow

def main():
    if 'user' not in st.session_state:
        login()
    else:
        if st.sidebar.button("Logout"):
            del st.session_state.user
            st.rerun()
        if st.session_state.user['role'] == 'manager':
            manager_view(st.session_state.user['station_id'])
        else:
            owner_view()

if __name__ == "__main__":
    main()
