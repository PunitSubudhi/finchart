import streamlit as st
import pandas as pd
import numpy as np
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_option_menu import option_menu
import openpyxl
import base64

st.set_page_config(layout="wide")

#st.write(st.session_state)
#Default Columns for Standardised financial data
st.session_state.fixed_columns: list[str] = ['Date', 'Description', 'Amount', 'Category', 'crdr','Balance']
st.session_state.parsed_df=None
parsed_df = pd.DataFrame(columns=st.session_state.fixed_columns)
columns = st.session_state.fixed_columns
st.session_state.col_map_dict = {col:None for col in columns}



st.markdown("### Please Upload your Transactions below to continue)")
# Upload File
file = st.file_uploader('Upload your Transactions here',
                        type=['csv', 'xlsx'],
                        help="All files are processed in your browser and not uploaded to any server",
                        accept_multiple_files=False,
                        key='uploaded_file',
                        label_visibility='collapsed')

# Check if file is uploaded
if file is not None:
    # Detect File Type
    #st.write(file.type)
    if file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_type = 'xlsx'
    elif file.type == 'text/csv':
        file_type = 'csv'
    #st.toast(f'File Type: {file_type}')
    
    # Load Data
    data = pd.read_csv(file) if file_type == 'csv' else pd.read_excel(file)
    data_columns: list = list(data.columns)
    data_types: list = list(data.dtypes.to_list())
    # Check if data is there
    if data.empty:
        st.error("No Data Found in the Uploaded File")
    else:
        #Date,Description, Amount, Category, Subcategory, Type = st.columns(6)
        num_rows,num_cols = data.shape
        st.toast(f"Data Loaded Successfully with {num_rows} rows and {num_cols} columns",icon='✅')
        discover_data_view = st.expander('Click here to view and discover data',expanded=False)
        with discover_data_view:
            st.dataframe(dataframe_explorer(data,case=False), use_container_width=True)

        # Ask user about Type of File in the uploaded file : Debit/Credit or +/-
        transaction_posted_type = st.radio("Select the Type of File in the Uploaded Data to continue",
                                           ['Debit/Credit','Plus/Minus'],
                                           key='file_type',
                                           horizontal=True,
                                           index=None)
        st.write(transaction_posted_type)
        st.session_state.transaction_posted_type = transaction_posted_type
        
        if transaction_posted_type == 'Plus/Minus':
            st.markdown("##### Please select the column that represents the Amount in the uploaded data",
                        help="This will help in determining the Credit/Debit status of the transaction")
            
            amount_column_name = st.selectbox("Select the Column that represents Amount",
                                              data_columns,
                                              key='amount_column',
                                              placeholder="Select the Column that represents Amount",
                                              label_visibility='collapsed',
                                              index=None)
            
            if amount_column_name is not None:
                try:
                    data['cr/dr'] = data[amount_column_name].apply(lambda x: 'Credit' if x > 0 else 'Debit')
                    data[amount_column_name] = data[amount_column_name].apply(lambda x: x if x > 0 else -x)
                    st.toast("adding Column cr/dr as Credit/Debit")
                except Exception as e:
                    st.error(f"Error in Adding Column cr/dr: {e}")
                    
        elif transaction_posted_type == 'Debit/Credit':
            amount_column_name = 'Amount'
            st.session_state.amount_column_name = amount_column_name
        else:
            amount_column_name = None
            
        #with st.expander(label="Data Columns and Data Types",expanded=False):
        # Check Data Columns and display it to the user
         #   st.write("Columns and data types in the Uploaded Data")
          #  st.dataframe(pd.DataFrame(np.array([data_types]),columns=data_columns,index=['Data Type']))
           # st.write ("Required Columns for Standardised financial data")
            #st.dataframe(pd.DataFrame(np.array([columns]),columns=columns,index=['Data Type']))
        #st.dataframe(pd.DataFrame(data=data_types,columns=data_columns,index=None),use_container_width=True)
        
        
        if amount_column_name is not None:
        
        # Ask User to map columns to existing column template
            st.markdown("#### Map Columns to existing column template")
            
            num_cols = len(columns)
            cols=st.columns(num_cols)
            rows=[st.columns([0.2,0.2,0.8]) for i in range(len(columns))]
            data_columns: list = list(data.columns)
            data_types: list = list(data.dtypes.to_list())
            
            for i , row in enumerate(rows):
                row[0].write(f"{columns[i]} maps to:")
                if columns[i] == 'crdr' and transaction_posted_type == 'Plus/Minus':
                    col_name = row[1].selectbox(f"{columns[i]} maps to:",data_columns,key=i,label_visibility='collapsed',index=len(data_columns)-1,disabled=True,help="This column is automatically added based on the Amount Column")
                else: 
                    col_name = row[1].selectbox(f"{columns[i]} maps to:",data_columns,key=i,label_visibility='collapsed',index=None)
                if col_name:
                    st.session_state.col_map_dict[columns[i]] = col_name
                    
            #st.write(st.session_state.col_map_dict)
            
            if st.button("continue"):
                try:
                    for key,value in st.session_state.col_map_dict.items():
                        if value != "":
                            parsed_df[key] = data[value]
                    st.session_state.parsed_df = parsed_df
                except Exception as e:
                    st.error(f"Error in mapping columns: {e}")
            
            # Parse Data and display random 5 rows to the user with a before and after view
            with st.expander(label="View / Download Parsed Data",expanded=False):
                c1,c2=st.columns([0.4,0.6])
                num_rows = c1.number_input("Number of Rows to Display",min_value=1,max_value=10,value=5)
                c2.dataframe(parsed_df.head(num_rows))

                # Give download option for the Processed Data
                csv = parsed_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="parsed_data.csv">Download Parsed Data</a>'
                c1.download_button("Download Parsed Data",data=csv,file_name="parsed_data.csv",mime="text/csv")
                c1.markdown(href, unsafe_allow_html=True)
            
            
            if st.session_state.parsed_df is not None:
                st.success("Data Parsed Successfully")
                # Add Button to continue to next page : Charts
                if st.button("Continue to Charts",key='Continue to Charts',help="Click to continue to the next page to view the charts"):
                    st.switch_page("pages/2_Charts.py") 
            # For any data that is not parsed, ask user to correct it with a option to download the wrong data
            # Add Button to continue to next page : Charts
            #st.button("Continue to Charts",key='Continue to Charts',help="Click to continue to the next page to view the charts",on_click=None)
            
            # Create charts for the parsed data