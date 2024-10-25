import base64
import os
import time
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from streamlit_extras.dataframe_explorer import dataframe_explorer
import openpyxl
import uuid
from custom_functions import *

#st.set_page_config(layout="wide", initial_sidebar_state='collapsed')

# Database Connection
DB_uri = (
    f"mongodb+srv://{st.secrets['DB_USERNAME']}:{st.secrets['DB_PASSWORD']}"
    f"@{st.secrets['DB_HOST']}/?retryWrites=true&w=majority&appName=Log"
)
client = MongoClient(DB_uri, server_api=ServerApi('1'))
log = client['logs']['log']

# Initialize log
if 'log' not in st.session_state:
    initialize_log()

# Default Columns for Standardised financial data
st.session_state.fixed_columns = ['Date', 'Description', 'Amount', 'Category', 'crdr', 'Balance']
columns = st.session_state.fixed_columns

st.session_state.parsed_df = None
parsed_df = pd.DataFrame(columns=st.session_state.fixed_columns)

st.session_state.col_map_dict = {col: None for col in columns}
st.session_state.log_status = False

flex_buttons()

# Navbar
navbar()

st.markdown("### Please Upload your Transactions below to continue")
log_action("Displayed upload prompt")
update_log_in_db(log)
# Upload File
file = st.file_uploader(
    'Upload your Transactions here',
    type=['csv', 'xlsx'],
    help="All files are processed in your browser and not uploaded to any server",
    accept_multiple_files=False,
    key='uploaded_file',
    label_visibility='collapsed'
)

# Check if file is uploaded
if file is not None:
    log_action(f"File uploaded: {file.name}")
    update_log_in_db(log)

    # Detect File Type
    if file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_type = 'xlsx'
    elif file.type == 'text/csv':
        file_type = 'csv'

    # Load Data
    try:
        data = pd.read_csv(file) if file_type == 'csv' else pd.read_excel(file)
        data_columns = list(data.columns)
        data_types = list(data.dtypes.to_list())
        log_action(f"Data loaded with {len(data)} rows and {len(data.columns)} columns")
        update_log_in_db(log)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        log_error(f"Error loading data: {e}")
        update_log_in_db(log)

    # Save the uploaded file in session state
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    st.session_state.uploaded_files[file.name] = {'raw': data.to_dict('records'), 'processed': None}

    # Check if data is there
    if data.empty:
        st.error("No Data Found in the Uploaded File")
        log_error("No Data Found in the Uploaded File")
        update_log_in_db(log)
    else:
        num_rows, num_cols = data.shape
        st.toast(f"Data Loaded Successfully with {num_rows} rows and {num_cols} columns", icon='✅')
        log_action(f"Data Loaded Successfully with {num_rows} rows and {num_cols} columns")
        update_log_in_db(log)

        discover_data_view = st.expander('Click here to view and discover data', expanded=False)
        with discover_data_view:
            st.dataframe(dataframe_explorer(data, case=False), use_container_width=True)

        # Ask user about Type of File in the uploaded file: Debit/Credit or +/-
        transaction_posted_type = st.radio(
            "Select the Type of File in the Uploaded Data to continue",
            ['Debit/Credit', 'Plus/Minus'],
            key='file_type',
            horizontal=True,
            index=None
        )

        if transaction_posted_type == 'Plus/Minus':
            st.markdown(
                "##### Please select the column that represents the Amount in the uploaded data",
                help="This will help in determining the Credit/Debit status of the transaction"
            )

            amount_column_name = st.selectbox(
                "Select the Column that represents Amount",
                data_columns,
                key='amount_column',
                placeholder="Select the Column that represents Amount",
                label_visibility='collapsed',
                index=None
            )

            if amount_column_name is not None:
                try:
                    data['cr/dr'] = data[amount_column_name].apply(lambda x: 'Credit' if x > 0 else 'Debit')
                    data[amount_column_name] = data[amount_column_name].apply(lambda x: x if x > 0 else -x)
                    st.toast("Adding Column cr/dr as Credit/Debit")
                    log_action("Added Column cr/dr as Credit/Debit")
                    update_log_in_db(log)
                except KeyError as e:
                    st.error(f"KeyError in Adding Column cr/dr: {e}")
                    log_error(f"KeyError in Adding Column cr/dr: {e}")
                    update_log_in_db(log)
                except TypeError as e:
                    st.error(f"TypeError in Adding Column cr/dr: {e}")
                    log_error(f"TypeError in Adding Column cr/dr: {e}")
                    update_log_in_db(log)
                except Exception as e:
                    st.error(f"Unexpected error in Adding Column cr/dr: {e}")
                    log_error(f"Unexpected error in Adding Column cr/dr: {e}")
                    update_log_in_db(log)

        elif transaction_posted_type == 'Debit/Credit':
            amount_column_name = 'Amount'
            st.session_state.amount_column_name = amount_column_name
            log_action("Transaction posted type is Debit/Credit")
            update_log_in_db(log)
        else:
            amount_column_name = None

        if amount_column_name is not None:
            # Ask User to map columns to existing column template
            st.markdown("#### Map Columns to existing column template")
            log_action("Prompted user to map columns")
            update_log_in_db(log)

            with st.form(key='column_mapping_form'):
                num_cols = len(columns)
                cols = st.columns(num_cols)

                data_columns = list(data.columns)
                data_types = list(data.dtypes.to_list())
                rows = [st.columns([0.2, 0.2, 0.8]) for _ in range(len(columns))]
                for i, row in enumerate(rows):
                    row[0].write(f"{columns[i]} maps to:")
                    if columns[i] == 'crdr' and transaction_posted_type == 'Plus/Minus':
                        col_name = row[1].selectbox(
                            f"{columns[i]} maps to:", data_columns, key=i, label_visibility='collapsed',
                            index=len(data_columns) - 1, disabled=True,
                            help="This column is automatically added based on the Amount Column"
                        )
                    else:
                        col_name = row[1].selectbox(f"{columns[i]} maps to:", data_columns, key=i, label_visibility='collapsed', index=None)
                    if col_name:
                        st.session_state.col_map_dict[columns[i]] = col_name

                submit_button = st.form_submit_button(label='Map Columns and show charts')

            if submit_button:
                try:
                    for key, value in st.session_state.col_map_dict.items():
                        if value != "":
                            parsed_df[key] = data[value]
                    st.session_state.log.update({'parsed_data_status': 'Data Parsed Successfully'})
                    st.session_state.log.update({'col_map_dict': st.session_state.col_map_dict})
                    st.session_state.parsed_df = parsed_df
                    st.session_state.uploaded_files[file.name]['processed'] = parsed_df.to_dict('records')
                    st.button(
                        "Continue to Charts", key='Continue to Charts',
                        help="Click to continue to the next page to view the charts", on_click=None
                    )
                    log_action("Mapped columns and parsed data successfully")
                    update_log_in_db(log)
                    #try_log(log) # Commented out to avoid errors
                    st.switch_page("pages/2_Charts.py")
                except KeyError as e:
                    st.session_state.log.update({'error': f"KeyError in mapping columns: {e}"})
                    st.error(f"KeyError in mapping columns: {e}")
                    log_error(f"KeyError in mapping columns: {e}")
                    update_log_in_db(log)
                except TypeError as e:
                    st.session_state.log.update({'error': f"TypeError in mapping columns: {e}"})
                    st.error(f"TypeError in mapping columns: {e}")
                    log_error(f"TypeError in mapping columns: {e}")
                    update_log_in_db(log)
                except Exception as e:
                    st.session_state.log.update({'error': f"Unexpected error in mapping columns: {e}"})
                    st.error(f"Unexpected error in mapping columns: {e}")
                    log_error(f"Unexpected error in mapping columns: {e}")
                    update_log_in_db(log)