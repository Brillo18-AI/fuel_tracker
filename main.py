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

    # 1. Station name
    st.markdown(f"### Station: **{station_id}**")

    with st.form(key="pump_report_form"):
        # 2. Date
        date = st.date_input("Date", datetime.now())

        # 3. Dropdowns
        tanks = ["Tank 1", "Tank 2", "Tank 3", "Tank 4"]
        pumps = ["Pump A", "Pump B", "Pump C", "Pump D"]

        selected_tank = st.selectbox("Select Tank", tanks)
        selected_pump = st.selectbox("Select Pump", pumps)

        # 4. Price
        price_per_liter = st.number_input("Price per Liter (₦)", min_value=0.0, format="%.2f")

        # 5. Meter readings
        open_meter = st.number_input("Open Meter Reading", min_value=0.0, format="%.2f")
        close_meter = st.number_input("Close Meter Reading", min_value=open_meter, format="%.2f")

        # 6. Expected Liters & Cash
        auto_liters = close_meter - open_meter
        auto_cash = auto_liters * price_per_liter

        expected_liters = st.number_input("Expected Liters", value=auto_liters, format="%.2f")
        expected_cash = st.number_input("Expected Cash (₦)", value=auto_cash, format="%.2f")

        # 7. Expenses & Cash at hand
        expenses = st.number_input("Expenses (₦)", min_value=0.0, format="%.2f")
        cash_at_hand = st.number_input("Cash at Hand (₦)", min_value=0.0, format="%.2f")

        # 8. Submit
        submitted = st.form_submit_button("Submit Report")

        if submitted:
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
    st.title("Owner Dashboard")

    # 1. Connect to sheet
    sheet = connect_to_sheet()
    if not sheet:
        st.error("Couldn't load data.")
        return

    # 2. Load pump reports
    try:
        records = sheet.worksheet("pump_reports").get_all_records()
    if not records:
        st.info("No reports available yet.")
        return
    df = pd.DataFrame(records)  # Moved up here
    except Exception as e:
        st.error(f"Failed to fetch reports: {e}")
    return

    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")  # Now safe to use df


    # 3. Date picker
    from_date = st.date_input("From date", datetime.now())
    df = df[df['date'] >= pd.to_datetime(from_date)]

    # 4. Station selector
    stations = df['station_id'].unique()
    
    if len(stations) == 0:
        st.warning("No stations found in data.")
        return

    selected_station = st.selectbox("Select Station", stations)
    station_df = df[df['station_id'] == selected_station]

    df = pd.DataFrame(records)
    st.write("DEBUG: Column names in df →", df.columns.tolist())

    if df.empty:
        st.info("No records for this station and date range.")
        return

    # 5. Sort by date descending
    df = df.sort_values(by="date", ascending=False).reset_index(drop=True)

    st.markdown("## 📋 Station Reports")

    # Display each row in a styled card
    for _, row in station_df.iterrows():
        st.markdown(f"""
        <div style="background-color: #fdfdfd; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); margin-bottom: 1.2rem; font-size: 0.95rem;">
            <h4 style="margin-top: 0;">🗓️ {row['date'].strftime('%Y-%m-%d')} — {row['tank']} / {row['pump']}</h4>
            <p><strong>Price per Litre:</strong> ₦{row['price_per_litre']:,.2f}</p>
            <p><strong>Open Meter:</strong> {row['open_meter']:,.2f}</p>
            <p><strong>Close Meter:</strong> {row['close_meter']:,.2f}</p>
            <p><strong>Expected Liters:</strong> {row['expected_liters']:,.2f} L</p>
            <p><strong>Expected Cash:</strong> <span style="color: #007BFF;">₦{row['expected_cash']:,.2f}</span></p>
            <p><strong>Expenses:</strong> <span style="color: #dc3545;">₦{row['expenses']:,.2f}</span></p>
            <p><strong>Cash at Hand:</strong> <span style="color: #28a745;">₦{row['cash_at_hand']:,.2f}</span></p>
        </div>
        """, unsafe_allow_html=True)

    # Totals Summary
    total_expected_cash = station_df['expected_cash'].sum()
    total_expenses = station_df['expenses'].sum()
    total_cash = station_df['cash_at_hand'].sum()

    st.markdown("## 🧾 Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Expected Cash Total", f"₦{total_expected_cash:,.2f}")
    col2.metric("Total Expenses", f"₦{total_expenses:,.2f}")
    col3.metric("Total Cash at Hand", f"₦{total_cash:,.2f}")

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
