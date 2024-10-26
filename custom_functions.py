import os
import uuid
import streamlit as st
import pandas as pd

def navbar():
    if st.session_state.get("username") is not None:
        st.write(f"Welcome, {st.session_state.username}")
    else: 
        st.write("Welcome to FinCharts, please login to retreive session state.")
    nav = st.columns([1, 1, 1])
    #Get relative path to pages folder
    for col,page in zip(nav, [file for file in os.listdir("pages")]):
        if col.button(f"Go to {page}",key=f"nav_{page}"):
            st.switch_page(f"pages/{page}")

def initialize_log():
    """Initialize a unique log entry for the session."""
    st.session_state.log = {
        'session_id': str(uuid.uuid4()),
        'actions': [],
        'errors': [],
        'date': pd.Timestamp.now()
    }
    st.session_state.log_id = None

def log_action(action, details=None):
    """Log an action in the session log."""
    log_entry = {
        'timestamp': pd.Timestamp.now(),
        'action': action
    }
    if details:
        log_entry['details'] = details
    st.session_state.log['actions'].append(log_entry)

def log_error(error, details=None):
    """Log an error in the session log."""
    log_entry = {
        'timestamp': pd.Timestamp.now(),
        'error': error
    }
    if details:
        log_entry['details'] = details
    st.session_state.log['errors'].append(log_entry)

def update_log_in_db(log):
    """Update the log entry in the database."""        
    try:
        result = log.update_one(
            {'session_id': st.session_state.log['session_id']},
            {'$set': st.session_state.log},
            upsert=True
        )
        if st.session_state.log_id is None:
            st.session_state.log_id = result.upserted_id
    except Exception as e:
        st.error(f"Error updating log in database: {e}")

def flex_buttons():
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

def save_session_state(username,session_collection):
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

def retrieve_session_state(username,session_collection):
    try:
        session_data = session_collection.find_one({"username": username})
        if session_data and "session_state" in session_data:
            for key, value in session_data["session_state"].items():
                st.session_state[key] = pd.DataFrame(value) if isinstance(value, list) and all(isinstance(i, dict) for i in value) else value
        st.toast("Session state retrieved from cloud.")
    except Exception as e:
        st.error(f"Error retrieving session state: {e}")


if __name__ == "__main__":
    navbar()