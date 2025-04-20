import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Page config
st.set_page_config(page_title="Fuel Tracker", layout="wide")

# Minimal CSS: make tables scrollable and enable pinch-zoom on mobile
st.markdown(
    """
    <style>
    /* Scrollable DataFrames */
    .stDataFrame, .stTable {
        max-width: 100% !important;
        overflow-x: auto !important;
    }

    /* Allow pinch-zoom on mobile devices */
    [data-testid="stAppViewContainer"] {
        touch-action: pinch-zoom !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
                    st.session_state.user = user
                    st.rerun()
            st.sidebar.error("Invalid credentials")

# Manager view

def manager_view(station_id):
    st.title(f"Station {station_id} Daily Report")
    with st.form("report_form"):
        date = st.date_input("Date", datetime.now())
        fuel = st.selectbox("Fuel Type", ["Petrol", "Diesel"])
        opening = st.number_input("Opening Stock (L)", min_value=0)
        received = st.number_input("Received Today (L)", min_value=0)
        sales = st.number_input("Sales (L)", min_value=0)
        closing = st.number_input("Closing Stock (L)", min_value=0)
        if st.form_submit_button("Submit"):
            sheet = connect_to_sheet()
            if sheet:
                rpt = sheet.worksheet("daily_reports")
                balance = opening + received - sales
                rpt.append_row([str(date), station_id, fuel, opening, received, sales, closing, balance])
                st.success("Report submitted!")
            else:
                st.error("Failed to save report")

# Owner view

def owner_view():
    st.title("All Stations Dashboard")
    sheet = connect_to_sheet()
    if sheet:
        recs = sheet.worksheet("daily_reports").get_all_records()
        from_date = st.date_input("From date", datetime.now())
        filtered = [r for r in recs if datetime.strptime(r['date'], "%Y-%m-%d").date() >= from_date]
        st.dataframe(filtered)
        st.write(f"Showing {len(filtered)} reports since {from_date}")
    else:
        st.error("Couldn't load data")

# Main flow

def main():
    if 'user' not in st.session_state:
        login()
    else:
        if st.sidebar.button("Logout"):
            del st.session_state.user
            st.experimental_rerun()
        if st.session_state.user['role'] == 'manager':
            manager_view(st.session_state.user['station_id'])
        else:
            owner_view()

if __name__ == "__main__":
    main()
