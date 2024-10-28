import streamlit as st
import pandas as pd
import numpy as np
from custom_functions import *
from upload_data import upload_data
from charts import show_charts
import time

print(initialise_db_conn())
if 'log' not in st.session_state:
    initialize_log()

st.title('Welcome to FinChart | A financial charting app')


if st.session_state.get('logged_in') is None or st.session_state.get('logged_in') == False:
    page_selected = st.navigation({
        "Manage Account": [
            st.Page(main, title="Manage Account"),
            st.Page(logout, title="Logout"),
        ]
    })
    page_selected.run()
else:
    page_selected = st.navigation({
        "Manage Account": [
            st.Page(logged_in_page, title="Manage Account"),
            st.Page(logout, title="Logout"),
        ],
        "View Charts": [
            st.Page(show_charts, title="View Charts"),
        ],
        "Upload Data": [
            st.Page(upload_data, title="Upload Transactions"),
        ]
    })
    page_selected.run()
   