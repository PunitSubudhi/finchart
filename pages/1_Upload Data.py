import streamlit as st
import pandas as pd
import numpy as np
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_option_menu import option_menu
import openpyxl
import base64

st.set_page_config(layout="wide")

# Default Columns for Standardised financial data
columns: list[str] = ['Date', 'Description', 'Amount', 'Category', 'Subcategory', 'cr/dr','Balance']
parsed_df = pd.DataFrame(columns=columns)

st.title('Upload your Transactions below to continue...')


c1,c2,c3 = st.columns([0.4,0.2,0.2])

# Upload File
file = c1.file_uploader('Upload your Transactions here', type=['csv', 'xlsx'])

with c3:
    if file is not None:
        selected = option_menu("Do you want to view the data?",['No',"Yes"],orientation='horizontal',icons=[' ',' '],menu_icon='menu',manual_select=True)

if file is not None:
    file_type = file.type
    # Detect File Type
    if file_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_type = 'xlsx'
    elif file_type == 'text/csv':
        file_type = 'csv'
    #st.toast(f'File Type: {file_type}')
    # Load Data
    data = pd.read_csv(file) if file_type == 'csv' else pd.read_excel(file)
    data_columns: list = list(data.columns)
    data_types: list = list(data.dtypes.to_list())
    # Check if data is there
    if data.empty:
        #st.toast("No Data Found in the Uploaded File")
        pass
    else:
        pass
        #st.toast("Data Loaded Successfully")
    
    #Date,Description, Amount, Category, Subcategory, Type = st.columns(6)
    num_rows,num_cols = data.shape
    
    c2.metric('Number of Rows', num_rows)
    c2.metric('Number of Columns', num_cols)
    
    
    if selected=='Yes':
        discover_data_view = st.expander('Discover Data',expanded=True)
        with discover_data_view:
            # Display Data
            explorer_df = dataframe_explorer(data,case=False)
            st.dataframe(explorer_df, use_container_width=True)


    # Ask user about Type of File in the uploaded file : Debit/Credit or +/-
    file_type = option_menu("Select the Type of Transaction Posting",['Debit/Credit','+/-'],orientation='horizontal',icons=[' ',' '],menu_icon='menu',manual_select=True)
    

    st.divider()
    with st.expander(label="Data Columns and Data Types",expanded=False):
    # Check Data Columns and display it to the user
        st.write("Columns and data types in the Uploaded Data")
        st.dataframe(pd.DataFrame(np.array([data_types]),columns=data_columns,index=['Data Type']))
        
        st.write ("Required Columns for Standardised financial data")
        st.dataframe(pd.DataFrame(np.array([columns]),columns=columns,index=['Data Type']))
        
    st.divider()
    #st.dataframe(pd.DataFrame(data=data_types,columns=data_columns,index=None),use_container_width=True)
    
    # Ask User to map columns to existing column template
    st.markdown("#### Map Columns to existing column template")
    
    dict_columns = {col:"" for col in columns}
    
    
    num_cols = len(columns)
    cols=st.columns(num_cols)
    
    if file_type == '+/-':
        try:
            amount_col = st.selectbox("Select the Column that represents Amount",data_columns)
            if amount_col:
                data['cr/dr'] = data[amount_col].apply(lambda x: 'Credit' if x > 0 else 'Debit')
                data[amount_col] = data[amount_col].apply(lambda x: x if x > 0 else -x)
                st.toast("adding Column cr/dr as Credit/Debit")
        except Exception as e:
            st.error(f"Error in Adding Column cr/dr: {e}")

    data_columns: list = list(data.columns)
    data_types: list = list(data.dtypes.to_list())
    
    for i , col in enumerate(cols):
        col.write(columns[i])
        col.write("maps to")
        col_name = col.selectbox("  ",data_columns,key=i,label_visibility='collapsed')
        if col_name:
            
            dict_columns[columns[i]] = col_name
    print(dict_columns)
    st.write(dict_columns)
    
    for key,value in dict_columns.items():
        if value != "":
            parsed_df[key] = data[value]
    
    
    # Parse Data and display random 5 rows to the user with a before and after view
    with st.expander(label="Parsed Data",expanded=False):
        st.write("Parsed Data Sample")
        num_rows = st.number_input("Number of Rows to Display",min_value=1,max_value=10,value=5)
        st.dataframe(parsed_df.head(num_rows))

        # Give download option for the Processed Data
        st.markdown("#### Download Parsed Data")
        st.markdown("Click the button below to download the parsed data")
        csv = parsed_df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="parsed_data.csv">Download Parsed Data</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        
    # For any data that is not parsed, ask user to correct it with a option to download the wrong data
    # Add Button to continue to next page : Charts
    #st.button("Continue to Charts",key='Continue to Charts',help="Click to continue to the next page to view the charts",on_click=None)
    
    # Create charts for the parsed data