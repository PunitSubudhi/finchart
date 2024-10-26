import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import hashlib
import pandas as pd
from custom_functions import *

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
                            st.rerun()
                        else:
                            st.error("Error registering user")
                            st.write(insert_user_response)
                except Exception as e:
                    st.error(f"Error during signup: {e}")

def login():
    with st.form(key="login_form"):
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            try:
                hashed_password = hash_password(password)
                user = users_collection.find_one({"username": username, "password": hashed_password})
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.toast("Logged in successfully!")
                    retrieve_session_state(username,session_collection)
                    return True
                else:
                    st.toast("Invalid username or password")
                    return False
                
            except Exception as e:
                st.toast(f"Error during login: {e}")



@st.fragment
def main():
    flex_buttons()
    if st.session_state.get("logged_in") is None or not st.session_state.logged_in:
        st.title("Welcome to FinCharts")
        st.write("""
        FinCharts allows you to upload and analyze your financial transactions. 
        To get started, please log in or sign up.
        
        **Features:**
        - **Login**: Access your account by entering your username and password.
        - **Signup**: Create a new account by providing a username and password.
        - **Sync State**: Save your current session state to the cloud.
        - **Retrieve State**: Retrieve your session state from the cloud.
        - **Logout**: Log out of your account.
        """)
        st.divider()
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
            save_session_state(st.session_state.username,session_collection)
        
        if cols[2].button("Retrieve State from Cloud"):
            retrieve_session_state(st.session_state.username,session_collection)
            
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
    main()