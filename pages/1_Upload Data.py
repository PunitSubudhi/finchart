import streamlit as st
import pandas as pd
import numpy as np
from streamlit_extras.dataframe_explorer import dataframe_explorer
import openpyxl
import base64
import plotly.express as px
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi




def show_charts():
    df = st.session_state.parsed_df
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
    
    # Plotting the data
    st.markdown("### Charts and Graphs")
    
    # Line chart for Balance over time
    st.markdown("#### Balance Over Time")
    fig_balance = px.line(df, x='Date', y='Balance', title='Balance Over Time')
    st.plotly_chart(fig_balance, use_container_width=True)
    
    # Bar chart for Amount by Category
    st.markdown("#### Amount by Category")
    fig_amount_category = px.bar(df, x='Category', y='Amount', title='Amount by Category', color='Category')
    st.plotly_chart(fig_amount_category, use_container_width=True)
    
    # Pie chart for Credit vs Debit
    st.markdown("#### Credit vs Debit")
    credit_debit_counts = df['crdr'].value_counts().reset_index()
    credit_debit_counts.columns = ['Type', 'Count']
    fig_credit_debit = px.pie(credit_debit_counts, names='Type', values='Count', title='Credit vs Debit')
    st.plotly_chart(fig_credit_debit, use_container_width=True)
    
    # Scatter plot for Amount vs Balance
    st.markdown("#### Amount vs Balance")
    fig_amount_balance = px.scatter(df, x='Amount', y='Balance', title='Amount vs Balance', color='Category')
    st.plotly_chart(fig_amount_balance, use_container_width=True)
    
    # Histogram for Amount distribution
    st.markdown("#### Amount Distribution")
    fig_amount_dist = px.histogram(df, x='Amount', title='Amount Distribution')
    st.plotly_chart(fig_amount_dist, use_container_width=True)

def try_log (log):
    try:
        # Add Date time to log
        st.session_state.log.update({'date':pd.Timestamp.now()})
        log.insert_one(st.session_state.log)
        st.session_state.log_status = True
    except Exception as e:
        st.error(f"Error in Logging: {e}")
        st.session_state.log_status = False

st.set_page_config(layout="wide")
# Database Connection
DB_uri = f"mongodb+srv://{st.secrets["DB_USERNAME"]}:{st.secrets["DB_PASSWORD"]}@{st.secrets["DB_HOST"]}/?retryWrites=true&w=majority&appName=Log"
client = MongoClient(DB_uri, server_api=ServerApi('1'))
log = client['logs']['log']

#st.write(st.session_state)
#Default Columns for Standardised financial data
st.session_state.fixed_columns: list[str] = ['Date', 'Description', 'Amount', 'Category', 'crdr','Balance']
columns = st.session_state.fixed_columns

st.session_state.parsed_df=None
parsed_df = pd.DataFrame(columns=st.session_state.fixed_columns)

st.session_state.col_map_dict = {col:None for col in columns}
st.session_state.log_status = False
st.session_state.log = {}



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
        st.session_state.log.update({'error':'No Data Found in the Uploaded File'})
    else:
        #Date,Description, Amount, Category, Subcategory, Type = st.columns(6)
        num_rows,num_cols = data.shape
        st.toast(f"Data Loaded Successfully with {num_rows} rows and {num_cols} columns",icon='✅')
        st.session_state.log.update({'data_load_status':f'Data Loaded Successfully with {num_rows} rows and {num_cols} columns'})
        discover_data_view = st.expander('Click here to view and discover data',expanded=False)
        with discover_data_view:
            st.dataframe(dataframe_explorer(data,case=False), use_container_width=True)

        # Ask user about Type of File in the uploaded file : Debit/Credit or +/-
        transaction_posted_type = st.radio("Select the Type of File in the Uploaded Data to continue",
                                           ['Debit/Credit','Plus/Minus'],
                                           key='file_type',
                                           horizontal=True,
                                           index=None)
        #st.write(transaction_posted_type)
        st.session_state.transaction_posted_type = transaction_posted_type
        st.session_state.log.update({'transaction_posted_type':transaction_posted_type})
        
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
                    st.session_state.log.update({'error':f"Error in Adding Column cr/dr: {e}"})
                    
                    
        elif transaction_posted_type == 'Debit/Credit':
            amount_column_name = 'Amount'
            st.session_state.amount_column_name = amount_column_name
        else:
            amount_column_name = None
            
        if amount_column_name is not None:
        
        # Ask User to map columns to existing column template
            st.markdown("#### Map Columns to existing column template")
            
            num_cols = len(columns)
            cols=st.columns(num_cols)
            
            data_columns: list = list(data.columns)
            data_types: list = list(data.dtypes.to_list())
            rows=[st.columns([0.2,0.2,0.8]) for i in range(len(columns))]
            for i , row in enumerate(rows):
                row[0].write(f"{columns[i]} maps to:")
                if columns[i] == 'crdr' and transaction_posted_type == 'Plus/Minus':
                    col_name = row[1].selectbox(f"{columns[i]} maps to:",data_columns,key=i,label_visibility='collapsed',index=len(data_columns)-1,disabled=True,help="This column is automatically added based on the Amount Column")
                else: 
                    col_name = row[1].selectbox(f"{columns[i]} maps to:",data_columns,key=i,label_visibility='collapsed',index=None)
                if col_name:
                    st.session_state.col_map_dict[columns[i]] = col_name
            
            
            if st.button("Map Columns and show charts",key='Map Columns'):
                try:
                    for key,value in st.session_state.col_map_dict.items():
                        if value != "":
                            parsed_df[key] = data[value]
                    st.session_state.log.update({'parsed_data_status':'Data Parsed Successfully'})
                    st.session_state.log.update({'col_map_dict':st.session_state.col_map_dict})
                    st.session_state.parsed_df = parsed_df
                    st.button("Continue to Charts",key='Continue to Charts',help="Click to continue to the next page to view the charts",on_click=None)
                    try_log(log)
                    st.switch_page("pages/2_Charts.py")
                except Exception as e:
                    st.session_state.log.update({'error':f"Error in mapping columns: {e}"})
                    st.error(f"Error in mapping columns: {e}")
                
                

