import os
import uuid
import streamlit as st
import pandas as pd
from pymongo.mongo_client import MongoClient
import hashlib
from pymongo.server_api import ServerApi

def continue_as_guest():
    st.session_state.logged_in = False
    st.session_state.clear()
    st.rerun()

def get_db_conn() -> dict:
    DB_uri = (
    f"mongodb+srv://{st.secrets['DB_USERNAME']}:{st.secrets['DB_PASSWORD']}"
    f"@{st.secrets['DB_HOST']}/?retryWrites=true&w=majority&appName=Log"
    )
    client = MongoClient(DB_uri, server_api=ServerApi('1'))
    log_table = client['logs']['log']
    users_collection = client['finchart']['users']
    session_collection = client['finchart']['sessions']
    #return client,log_table,users_collection,session_collection
    return {
        "client": client,
        "log_table": log_table,
        "users_collection": users_collection,
        "session_collection": session_collection
    }

def initialise_db_conn() -> bool:
    db_conn_dict = get_db_conn()
    st.session_state.client = db_conn_dict["client"]
    st.session_state.log_table = db_conn_dict["log_table"]
    st.session_state.users_collection = db_conn_dict["users_collection"]
    st.session_state.session_collection = db_conn_dict["session_collection"]
    
    #Test connection
    try:
        st.session_state.client.server_info()
        #st.success("Database connection successful.")
        return True
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return False
    if 'log' not in st.session_state:
        initialize_log()
    
def navbar() -> None:
    """
    if st.session_state.get("username") is not None:
        st.write(f"Welcome, {st.session_state.username}")
    else: 
        st.write("Welcome to FinCharts, please login to retreive session state.")
    nav = st.columns([1, 1, 1])
    #Get relative path to pages folder
    for col,page in zip(nav, [file for file in os.listdir("pages")]):
        if col.button(f"Go to {page}",key=f"nav_{page.split('.')[0]}"):
            st.toast(f"nav_{page}-{uuid.uuid1()}")
            st.switch_page(f"pages/{page}")"""
    pass

def initialize_log() -> None:
    """Initialize a unique log entry for the session."""
    st.session_state.log = {
        'session_id': str(uuid.uuid4()),
        'actions': [],
        'errors': [],
        'date': pd.Timestamp.now()
    }
    st.session_state.log_id = None

def log_action(action, details=None, update_db=False)   -> None:
    """Log an action in the session log."""
    log_entry = {
        'timestamp': pd.Timestamp.now(),
        'action': action
    }
    if details:
        log_entry['details'] = details
    st.session_state.log['actions'].append(log_entry)
    
    if update_db:
        update_log_in_db(st.session_state.log)
    

def log_error(error, details=None) -> None:
    """Log an error in the session log."""
    log_entry = {
        'timestamp': pd.Timestamp.now(),
        'error': error
    }
    if details:
        log_entry['details'] = details
    st.session_state.log['errors'].append(log_entry)

def update_log_in_db(log) -> None:
    """Update the log entry in the database."""        
    try:
        result = st.session_state.log_table.update_one(
            {'session_id': st.session_state.log['session_id']},
            {'$set': st.session_state.log},
            upsert=True
        )
        if st.session_state.log_id is None:
            st.session_state.log_id = result.upserted_id
    except Exception as e:
        st.error(f"Error updating log in database: {e}")

def flex_buttons() -> None:
    st.markdown("""
            <style>
                div[data-testid="column"] {
                    width: fit-content !important;
                    flex: unset;
                }
                div[data-testid="column"] * {
                    width: fit-content !important;
                }
            </style>
            """, unsafe_allow_html=True)

def save_session_state(username) -> None:
    try:
        session_data = {key: value.to_dict('records') if isinstance(value, pd.DataFrame) else value for key, value in st.session_state.items()}
        print(session_data.pop("client", None))
        session_data.pop("log_table", None)
        session_data.pop("users_collection", None)
        session_data.pop("session_collection", None)
        session_data.pop("log", None)
        session_data.pop("log_id", None)
        session_data.pop("logged_in", None)
        session_data.pop("username", None)
        st.write(session_data)
        st.session_state.session_collection.update_one(
            {"username": username},
            {"$set": {"session_state": session_data}},
            upsert=True
        )
        st.success("Session state synced with cloud.")
    except Exception as e:
        st.error(f"Error saving session state: {e}")
        print(e)

def retrieve_session_state(username):
    try:
        session_data = st.session_state.session_collection.find_one({"username": username})
        if session_data and "session_state" in session_data:
            for key, value in session_data["session_state"].items():
                st.session_state[key] = pd.DataFrame(value) if isinstance(value, list) and all(isinstance(i, dict) for i in value) else value
        st.toast("Session state retrieved from cloud.")
    except Exception as e:
        st.error(f"Error retrieving session state: {e}")

def hash_password(password) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def signup() -> bool:
    with st.form(key="signup_form"):
        st.title("Signup")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Signup"):
            if password != confirm_password:
                st.error("Passwords do not match!")
            else:
                try:
                    hashed_password = hash_password(password)
                    user = {"username": username, "password": hashed_password}
                    # Check if username exists: 
                    if users_collection.find_one({"username": username}):
                        st.error("Username already exists!")
                    else:
                        insert_user_response = users_collection.insert_one(user)
                        # Check if the user was inserted successfully
                        if insert_user_response.acknowledged:
                            st.success("User registered successfully! Please login.")
                            st.write(insert_user_response)
                            return True
                        else:
                            st.error("Error registering user")
                            st.write(insert_user_response)
                            return False
                except Exception as e:
                    st.error(f"Error during signup: {e}")

def login() -> bool:
    with st.form(key="login_form"):
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            try:
                hashed_password = hash_password(password)
                user = st.session_state.users_collection.find_one({"username": username, "password": hashed_password})
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.toast("Logged in successfully!")
                    retrieve_session_state(username)
                    return True
                else:
                    st.toast("Invalid username or password")
                    return False
                
            except Exception as e:
                st.toast(f"Error during login: {e}")

def logout() -> None:
    st.popover("Are you sure you want to logout?")
    st.session_state.logged_in = False
    st.session_state.clear()
    st.rerun()

def logged_in_page():
    flex_buttons()
    st.write(f"## Welcome, {st.session_state.username}!")
    #st.sidebar.write(f"Logged in as {st.session_state.username}")
    if st.session_state.get("logged_in") is None or not st.session_state.logged_in:
        option = st.radio("Choose an option", ["Login", "Signup"],index=0,horizontal=True,key="login_signup")
        if option == "Login":
            if login():
                st.rerun()
        elif option == "Signup":
            signup()
    else:
        cols = st.columns(4)
        if cols[0].button("Logout"):
            logout()
        
        if cols[1].button("Sync Current State with Cloud"):
            save_session_state(st.session_state.username)
        
        if cols[2].button("Retrieve State from Cloud"):
            retrieve_session_state(st.session_state.username)
            
        if cols[3].button("Clear Session State and logout"):
            st.session_state.logged_in = False
            st.session_state.clear()
            st.rerun()
        
        #Butons to navigate to pages
        navbar()

@st.fragment
def main():
    flex_buttons()
        
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        #st.sidebar.write("Please login to access the app.")

    if st.session_state.logged_in:
        st.write(f"## Welcome, {st.session_state.username}!")
        #st.sidebar.write(f"Logged in as {st.session_state.username}")
        
        cols = st.columns(4)
        if cols[0].button("Logout"):
            st.session_state.logged_in = False
            st.session_state.clear()
            st.rerun()
        
        if cols[1].button("Sync Current State with Cloud"):
            save_session_state(st.session_state.username)
        
        if cols[2].button("Retrieve State from Cloud"):
            retrieve_session_state(st.session_state.username)
            
        if cols[3].button("Clear Session State and logout"):
            st.session_state.logged_in = False
            st.session_state.clear()
            st.rerun()
        
        #Butons to navigate to pages
        navbar()
    else:
        option = st.radio("Choose an option", ["Login", "Signup"],index=0,horizontal=True,key="login_signup")
        if option == "Login":
            if login():
                st.rerun()
        elif option == "Signup":
            signup()


if __name__ == "__main__":
    navbar()