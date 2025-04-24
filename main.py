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
    raw = st.text_input(label, value=f"{default:,}", key=key)
    try:
        return int(raw.replace(",", ""))
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


# Manager view with inputs for four tanks
def manager_view(station_id):
    st.title(f"Station {station_id} Daily Report")
    price_per_liter = st.number_input("Price per Liter (₦)", min_value=0.0, format="%.2f")
    
    # List of four tanks per station
    tanks = ["Tank 1", "Tank 2", "Tank 3", "Tank 4"]
    with st.form(key="report_form"):
        date = st.date_input("Date", datetime.now())
        # Collect inputs per tank
        tank_data = {}
        for tank in tanks:
            st.subheader(tank)
            opening = formatted_number_input(f"{tank} Opening Stock (L)", f"{tank}_opening")
            received = formatted_number_input(f"{tank} Received Today (L)", f"{tank}_received")
            sales = formatted_number_input(f"{tank} Sales (L)", f"{tank}_sales")
            closing = formatted_number_input(f"{tank} Closing Stock (L)", f"{tank}_closing")

            tank_data[tank] = {
                "opening": opening,
                "received": received,
                "sales": sales,
                "closing": closing
            }
        if st.form_submit_button("Submit Report"):
            sheet = connect_to_sheet()
            if sheet:
                ws = sheet.worksheet("daily_reports")
                for tank, data in tank_data.items():
                    balance = data['opening'] + data['received'] - data['sales']
                    revenue = price_per_liter * data['sales']
                    ws.append_row([
                        date.strftime("%Y-%m-%d"),
                        station_id,
                        tank,
                        data['opening'],
                        data['received'],
                        data['sales'], 
                        data['closing'],
                        balance, 
                        price_per_liter, 
                        revenue
                    ])
                st.success("All tank reports submitted successfully!")
            else:
                st.error("Failed to save reports.")

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
               
            display_df = tank_df[['date', 'opening', 'recieved', 'sales', 'closing', 'balance', 'revenue']].copy()
            # Format numeric columns with comma separation
            for col in ['opening', 'recieved', 'sales', 'closing', 'balance']:
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)
            for col in ['price', 'revenue']:
                display_df[col] = display_df[col].apply(lambda x: f"₦{x:,.2f}" if isinstance(x, (int, float)) else x)

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
