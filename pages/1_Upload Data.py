import streamlit as st
import pandas as pd
import numpy as np
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_option_menu import option_menu

st.set_page_config(layout="wide")

# Default Columns for Standardised financial data
columns = ['Date', 'Description', 'Amount', 'Category', 'Subcategory', 'Type']

st.title('Upload your Transactions below to continue...')

# Upload File
file = st.file_uploader('Upload your Transactions here', type=['csv', 'xlsx'])
# Detect File Type
if file is not None:
    file_type = file.type
    if file_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_type = 'xlsx'
    elif file_type == 'text/csv':
        file_type = 'csv'
    st.toast(f'File Type: {file_type}')
    # Load Data
    data = pd.read_csv(file) if file_type == 'csv' else pd.read_excel(file)
    
    
    #Date,Description, Amount, Category, Subcategory, Type = st.columns(6)
    num_rows,num_cols = data.shape
    rows,cols,rest = st.columns([0.2,0.2,0.6])
    rows.metric('Number of Rows', num_rows)
    cols.metric('Number of Columns', num_cols)
    
    with rest:
        selected = option_menu("Explore Data ? ",['No',"Yes"],orientation='horizontal',icons=['yes','no'])
    
    if selected == 'Yes':
        # Display Data
        explorer_df = dataframe_explorer(data,case=False)
        st.dataframe(explorer_df, use_container_width=True)
    else:
        pass

    # Ask user about Type of File in the uploaded file : Debit/Credit or +/-

    # Check Data Columns and display it to the user
    # Ask User to map columns to existing column template
    # Parse Data and display first 5 rows to the user with a before and after view
    # For any data that is not parsed, ask user to correct it with a option to download the wrong data
    # Add Button to continue to next page : Charts