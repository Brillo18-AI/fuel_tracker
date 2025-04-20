import streamlit as st
from datetime import datetime
from urllib.parse import quote
import gspread
from google.oauth2.service_account import Credentials

# Configure page
st.set_page_config(page_title="Fuel Tracker", layout="wide")

# Single CSS injection for zoom and theme
st.markdown("""
<style>
  /* Enable pinch-zoom responsiveness on mobile */
  html, body {
    touch-action: manipulation;
    -webkit-text-size-adjust: 100%;
    zoom: 1.0 !important;
    transform: scale(1) !important;
    transform-origin: top left;
    overflow: auto;
  }
  /* Make tables scrollable and scalable */
  .stDataFrame, .stTable {
    width: 100% !important;
    overflow-x: auto !important;
    transform: scale(1) !important;
  }
  /* Theme: white background + green accents */
  .stApp { background-color: #ffffff !important; }
  h1, h2, h3, h4, h5, h6 { color: #4CAF50 !important; }
  .stButton>button { background-color: #4CAF50 !important; color: #fff !important; border-radius: 5px; }
  .stButton>button:hover { background-color: #45a049 !important; }
</style>
""", unsafe_allow_html=True)

# Google Sheets connection helper
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

# Authentication (Sidebar)
def login():
    st.sidebar.title("BINAC OIL LIMITED FUEL TRACKER")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        sheet = connect_to_sheet()
        if sheet:
            users = sheet.worksheet("users").get_all_records()
            user = authenticate(username, password, users)
            if user:
                st.session_state.user = user
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid credentials")

# Helper to validate credentials
def authenticate(username, password, users):
    for u in users:
        if u['username'].strip().lower() == username.strip().lower() and \
           u['password'].strip() == password.strip():
            return u
    return None

# Manager view: submit daily report
def manager_view(station_id):
    st.title(f"Station {station_id} Daily Report")
    with st.form("report_form"):
        date = st.date_input("Date", datetime.now())
        fuel_type = st.selectbox("Fuel Type", ["Petrol", "Diesel"])
        opening = st.number_input("Opening Stock (L)", min_value=0)
        received = st.number_input("Received Today (L)", min_value=0)
        sales = st.number_input("Sales (L)", min_value=0)
        closing = st.number_input("Closing Stock (L)", min_value=0)
        if st.form_submit_button("Submit"):
            sheet = connect_to_sheet()
            if sheet:
                report = sheet.worksheet("daily_reports")
                balance = opening + received - sales
                report.append_row([str(date), station_id, fuel_type, opening, received, sales, closing, balance])
                st.success("Report submitted!")
            else:
                st.error("Failed to save report")

# Owner view: display all station reports
def owner_view():
    st.title("All Stations Dashboard")
    sheet = connect_to_sheet()
    if sheet:
        records = sheet.worksheet("daily_reports").get_all_records()
        min_date = st.date_input("From date", datetime.now())
        filtered = [r for r in records if datetime.strptime(r['date'], "%Y-%m-%d").date() >= min_date]
        st.dataframe(filtered)
        st.write(f"Showing {len(filtered)} reports since {min_date}")
    else:
        st.error("Couldn't load data")

# Main application flow
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
