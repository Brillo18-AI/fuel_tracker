# main.py
import streamlit as st
from datetime import datetime
from urllib.parse import quote
from streamlit import title




# Custom white/green theme
def set_theme():
    st.markdown("""
    <style>
        
        /* Submit button */
        .stButton>button {
        background-color: #4CAF50 !important;
        color: white !important;
        border-radius: 5px !important;
        border: none !important;
        }
    
        /* Button hover effect */
        .stButton>button:hover {
        background-color: #45a049 !important;
        }
        /* Text inputs (black text + visible cursor) */
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
        color: #000000 !important;
        caret-color: #000000 !important;  /* Cursor color */
        }
        /* All regular text */
        p, div[data-testid="stMarkdown"], .stMarkdown, .stText {
        color: #000000 !important;  /* Pure black */
        }
        
        /* Password field cursor */
        input[type="password"] {
        caret-color: #000000 !important;
        }
        /* Text input - black text on white background */
        .stTextInput input {
            color: black !important;
            background-color: white !important;
        }
        
        /* Password input - black text on white background */
        .stTextInput[data-baseweb="input"] input {
            color: black !important;
            background-color: white !important;
        }
        
        /* Number input - black text on white background */
        .stNumberInput input {
            color: black !important;
            background-color: white !important;
        }
        
        /* Input label color */
        .stTextInput label, .stNumberInput label {
            color: black !important;
        }
        /* Main background */
        .stApp {
            background-color: white;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #4CAF50 !important;  /* Medium green */
        }

        /* Buttons */
        .stButton>button {
            background-color: #4CAF50;  /* Medium green */
            color: white;
            border-radius: 5px;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #f0fff0 !important;  /* Light green tint */
        }

        /* Input fields focus */
        .stTextInput>div>div>input:focus, 
        .stNumberInput>div>div>input:focus {
            border-color: #4CAF50 !important;
        }
        

        /* Success messages */
        .stAlert [data-testid="stMarkdown"] {
            color: #006400 !important;
        }
        /* Number input controls */
        button.step-up { background-color: #4CAF50 !important; }
        button.step-down { background-color: #4CAF50 !important; }
    
        /* Plus/minus icons */
        button.step-up:after { border-bottom-color: white !important; }
        button.step-down:after { border-top-color: white !important; } 
        
            /* Date picker */
        .stDateInput>div>div>input {
        background-color: #e8f5e9 !important;  /* Light green */
        border-color: #4CAF50 !important;
        }
    
        /* Select box (fuel type) */
        .stSelectbox>div>div>div {
        background-color: #e8f5e9 !important;
        border-color: #4CAF50 !important;
        }
    
        /* Dropdown arrow */
        .stSelectbox>div>div>div>svg {
        fill: #4CAF50 !important;
        } 
    </style>
    """, unsafe_allow_html=True)


# Add to your set_theme() function
st.markdown("""
<style>
    /* Tables */
    .stDataFrame {
        border: 1px solid #4CAF50 !important;
    }

    /* Selected rows */
    table tbody tr:hover {
        background-color: #f0fff0 !important;
    }
    /* Main green palette */
    :root {
        --primary-green: #4CAF50;
            --light-green: #e8f5e9;
            --dark-green: #2E7D32;
        }
        
    /* Apply to all interactive elements */
    .stButton>button,
    .stDateInput>div>div>input,
    .stSelectbox>div>div>div,
    button.step-up,
    button.step-down {
    transition: all 0.3s ease !important;
    }
        
    /* Focus states */
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus {
    border-color: var(--primary-green) !important;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Call this function right after your imports
set_theme()


import gspread
from google.oauth2.service_account import Credentials
def connect_to_sheet():
    try:
        creds_info = st.secrets["google_service_account"]
        scopes = ['https://googleapis.com/auth/spreadsheets',
                  'https://googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open("FuelTracker")
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        st.info("Please ensure: 1) APIs are enabled 2) Sheet is shared 3) creds.json exists")
        return None

# Basic authentication

def login():
    st.sidebar.title("BINAC OIL LIMITED FUEL TRACKER")
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        try:
            sheet = connect_to_sheet()
            users = sheet.worksheet("users").get_all_records()

            for user in users:
                db_user = user["username"].strip().lower()
                db_pass = user["password"].strip()

                if db_user == username.strip().lower() and db_pass == password.strip():
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.sidebar.error("Invalid credentials")
        except Exception as e:
                        st.sidebar.error(f"Connection error: {e}")

    def authenticate(username, password):
        sheet = connect_to_sheet()
        users_sheet = sheet.worksheet("users")
        users = users_sheet.get_all_records()

        for user in users:
            # Trim whitespace from both sides
            db_user = user['username'].strip()
            db_pass = user['password'].strip()

            if db_user == username.strip() and db_pass == password.strip():
                return user
        return None
        # In authenticate():




# Manager view - ultra simple
def manager_view(station_id):
    st.title(f"Station {station_id} Daily Report")

    with st.form("report_form"):
        date = st.date_input("Date", datetime.now())
        fuel_type = st.selectbox("Fuel Type", ["Petrol", "Diesel"])
        opening = st.number_input("Opening Stock (Liters)", min_value=0)
        received = st.number_input("Received Today (Liters)", min_value=0)
        sales = st.number_input("Sales (Liters)", min_value=0)
        closing = st.number_input("Closing Stock (Liters)", min_value=0)

        if st.form_submit_button("Submit"):
            try:
                sheet = connect_to_sheet()
                report_sheet = sheet.worksheet("daily_reports")

                report_sheet.append_row([
                    str(date), station_id, fuel_type,
                    opening, received, sales, closing,
                    opening + received - sales  # auto-calculated balance
                ])
                st.success("Report submitted!")
            except:
                st.error("Failed to save report")


# Owner view - simple table
def owner_view():
    st.title("All Stations Dashboard")

    try:
        sheet = connect_to_sheet()
        reports = sheet.worksheet("daily_reports").get_all_records()

        # Simple filter by date
        min_date = st.date_input("From date", datetime.now())
        filtered = [r for r in reports if datetime.strptime(r["date"], "%Y-%m-%d").date() >= min_date]

        st.dataframe(filtered)

        # Basic summary
        st.write(f"Showing {len(filtered)} reports since {min_date}")
    except:
        st.error("Couldn't load data")


# Main app flow
def main():
    if "user" not in st.session_state:
        login()
    else:
        if st.sidebar.button("Logout"):
            del st.session_state.user
            st.rerun()

        if st.session_state.user["role"] == "manager":
            manager_view(st.session_state.user["station_id"])
        else:
            owner_view()


if __name__ == "__main__":
    main()
