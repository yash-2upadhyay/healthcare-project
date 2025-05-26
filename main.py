import streamlit as st
from pymongo import MongoClient
import streamlit_authenticator as stauth
import bcrypt
from cryptography.fernet import Fernet
from datetime import datetime, timezone
from web_functions import load_data
from Tabs import diagnosis, home, result, kc, talk2doc
from utils import store_user_query

# Set page configuration as the first Streamlit command
st.set_page_config(
    page_title="Diabetes Prediction System",
    page_icon="🥯",
    layout="wide",
    initial_sidebar_state="auto"
)

# Connect to MongoDB
try:
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db = client["diabetes_app"]
    users_collection = db["users"]
except Exception as e:
    st.error(f"Error connecting to MongoDB: {e}")
    st.stop()

# Load encryption key for query encryption
try:
    key = st.secrets["encryption"]["key"].encode()
    cipher = Fernet(key)
except KeyError as e:
    st.error(f"Error loading encryption key: {e}")
    st.stop()

def load_users():
    users = {}
    try:
        for user_doc in users_collection.find():
            users[user_doc["username"].lower()] = {
                "name": user_doc["name"],
                "password": user_doc["hashed_password"]
            }
        return users
    except Exception as e:
        st.error(f"Error loading users from database: {e}")
        return {}

def signup_page():
    st.title("📝 User Sign-Up")

    with st.form("signup_form", clear_on_submit=True):
        name = st.text_input("Full Name", key="signup_name")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        submit = st.form_submit_button("Sign Up")

    if submit:
        try:
            if not (name and username and password and confirm_password):
                st.warning("Please fill out all fields.")
                return
            if password != confirm_password:
                st.error("Passwords do not match!")
                return
            username_lower = username.lower()
            if users_collection.find_one({"username": username_lower}):
                st.error("Username already exists. Try another.")
                return

            # Hash password using streamlit-authenticator's Hasher
            hasher = stauth.Hasher()
            hashed_password = hasher.hash(password)
            hashed_password = hashed_password[0] if isinstance(hashed_password, list) else hashed_password

            user_doc = {
                "name": name,
                "username": username_lower,
                "hashed_password": hashed_password,
                "created_at": datetime.now(timezone.utc)
            }
            users_collection.insert_one(user_doc)
            st.success("✅ Account created successfully! You can now log in.")
        except Exception as e:
            st.error(f"Error during signup: {e}")

def login_page():
    st.title("🔐 Login")

    # Clear authenticator from session state to avoid conflicts
    if "authenticator" in st.session_state:
        del st.session_state["authenticator"]

    users = load_users()
    if not users:
        st.warning("No users found. Please sign up first!")
        return False, None, None

    # Prepare credentials for streamlit-authenticator
    credentials = {
        "usernames": {
            username: {
                "name": user["name"],
                "password": user["password"]
            }
            for username, user in users.items()
        }
    }

    # Initialize authenticator
    try:
        authenticator = stauth.Authenticate(
            credentials=credentials,
            cookie_name="diabetes_app",
            cookie_key="auth_key_123",  # Fixed key for consistency
            cookie_expiry_days=30
        )
        st.session_state["authenticator"] = authenticator
    except Exception as e:
        st.error(f"Error initializing authenticator: {e}")
        return False, None, None

    # Render login form
    try:
        result = authenticator.login(key="login_form")
        if isinstance(result, tuple) and len(result) == 2:
            username, name = result
            username_lower = username.lower()
            st.session_state["username"] = username_lower
            st.session_state["name"] = name
            st.session_state["logged_in"] = True
            st.success(f"Welcome {name}!")
            return True, username_lower, name
        elif result is False:
            st.error("Username/password incorrect")
            return False, None, None
        else:
            # Fallback manual login form
            st.subheader("Manual Login (Fallback)")
            with st.form("manual_login_form"):
                manual_username = st.text_input("Username", key="manual_login_username")
                manual_password = st.text_input("Password", type="password", key="manual_login_password")
                login_submit = st.form_submit_button("Login")

                if login_submit:
                    manual_username_lower = manual_username.lower()
                    if manual_username_lower in credentials["usernames"]:
                        stored_hash = credentials["usernames"][manual_username_lower]["password"].encode('utf-8')
                        if bcrypt.checkpw(manual_password.encode('utf-8'), stored_hash):
                            st.session_state["username"] = manual_username_lower
                            st.session_state["name"] = credentials["usernames"][manual_username_lower]["name"]
                            st.session_state["logged_in"] = True
                            st.success(f"Welcome {st.session_state['name']}!")
                            return True, manual_username_lower, st.session_state['name']
                        else:
                            st.error("Username/password incorrect")
                    else:
                        st.error("Username not found")
                    return False, None, None
            return False, None, None
    except Exception as e:
        st.error(f"Login error: {e}")
        return False, None, None

def logout():
    try:
        if "authenticator" in st.session_state:
            st.session_state["authenticator"].logout("Logout", "sidebar", key="logout_button")
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["name"] = None
        if "authenticator" in st.session_state:
            del st.session_state["authenticator"]
        st.success("Logged out successfully!")
        # Instead of rerun, set page to Login
        st.session_state["page"] = "Login"
    except Exception as e:
        st.error(f"Error during logout: {e}")

# --- MAIN APP ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["name"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Login"  # Default to Login page

# Sidebar navigation
if not st.session_state["logged_in"]:
    st.sidebar.title("Navigation")
    if st.sidebar.button("🔐 Login", key="login_button"):
        st.session_state["page"] = "Login"
    if st.sidebar.button("📝 Sign Up", key="signup_button"):
        st.session_state["page"] = "Sign Up"
else:
    st.sidebar.title("Navigation")
    st.session_state["page"] = st.sidebar.radio(
        "Select a page",
        ["Home", "Ask Queries", "Diagnosis", "Result", "Knowledge Center", "Logout"],
        key="nav_main"
    )

# Page rendering
if st.session_state["page"] == "Sign Up":
    signup_page()
elif st.session_state["page"] == "Login":
    if not st.session_state["logged_in"]:
        logged_in, username, name = login_page()
        if logged_in:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["name"] = name
            st.session_state["page"] = "Home"  # Redirect to Home after login
elif st.session_state["page"] == "Logout":
    logout()
else:
    if not st.session_state["logged_in"]:
        st.warning("Please login or sign up first!")
        st.session_state["page"] = "Login"
    else:
        Tabs = {
            "Home": home,
            "Ask Queries": talk2doc,
            "Diagnosis": diagnosis,
            "Result": result,
            "Knowledge Center": kc
        }

        st.sidebar.info("Made with Yash Upadhyay")

        try:
            df, X, y = load_data()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()

        if st.session_state["page"] == "Diagnosis":
            Tabs[st.session_state["page"]].app(df, X, y)
        else:
            Tabs[st.session_state["page"]].app()