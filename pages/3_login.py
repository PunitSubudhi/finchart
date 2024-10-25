import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import hashlib
import pandas as pd

# Database Connection
DB_uri = (
    f"mongodb+srv://{st.secrets['DB_USERNAME']}:{st.secrets['DB_PASSWORD']}"
    f"@{st.secrets['DB_HOST']}/?retryWrites=true&w=majority&appName=Log"
)
client = MongoClient(DB_uri, server_api=ServerApi('1'))
users_collection = client['finchart']['users']
session_collection = client['finchart']['sessions']

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup():
    st.title("Signup")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Signup"):
        if password != confirm_password:
            st.error("Passwords do not match!")
        else:
            try:
                hashed_password = hash_password(password)
                user = {"username": username, "password": hashed_password}
                users_collection.insert_one(user)
                st.success("User registered successfully! Please login.")
            except Exception as e:
                st.error(f"Error during signup: {e}")

def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        try:
            hashed_password = hash_password(password)
            user = users_collection.find_one({"username": username, "password": hashed_password})
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Logged in successfully!")
                retrieve_session_state(username)
            else:
                st.error("Invalid username or password")
        except Exception as e:
            st.error(f"Error during login: {e}")

def save_session_state(username):
    try:
        session_data = {key: value.to_dict('records') if isinstance(value, pd.DataFrame) else value for key, value in st.session_state.items()}
        session_collection.update_one(
            {"username": username},
            {"$set": {"session_state": session_data}},
            upsert=True
        )
        st.success("Session state synced with cloud.")
    except Exception as e:
        st.error(f"Error saving session state: {e}")

def retrieve_session_state(username):
    try:
        session_data = session_collection.find_one({"username": username})
        if session_data and "session_state" in session_data:
            for key, value in session_data["session_state"].items():
                st.session_state[key] = pd.DataFrame(value) if isinstance(value, list) and all(isinstance(i, dict) for i in value) else value
        st.success("Session state retrieved from cloud.")
    except Exception as e:
        st.error(f"Error retrieving session state: {e}")

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if st.session_state.logged_in:
        st.write(f"Welcome, {st.session_state.username}!")
        
        if st.button("Logout"):
            st.session_state.logged_in = False
        
        if st.button("Sync Current State with Cloud"):
            save_session_state(st.session_state.username)
        
        if st.button("Retrieve State from Cloud"):
            retrieve_session_state(st.session_state.username)
    else:
        option = st.selectbox("Choose an option", ["Login", "Signup"])
        if option == "Login":
            login()
        elif option == "Signup":
            signup()

if __name__ == "__main__":
    main()