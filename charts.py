import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_option_menu import option_menu
import openpyxl
import base64
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from custom_functions import *

# Database Connection
DB_uri = (
    f"mongodb+srv://{st.secrets['DB_USERNAME']}:{st.secrets['DB_PASSWORD']}"
    f"@{st.secrets['DB_HOST']}/?retryWrites=true&w=majority&appName=Log"
)
client = MongoClient(DB_uri, server_api=ServerApi('1'))
log = client['logs']['log']

flex_buttons()
navbar()

# Initialize log if not already initialized
if 'log' not in st.session_state:
    initialize_log()

def show_charts():
# Check if Session State has uploaded files
    if 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
        # Ask user to upload data and go through the steps
        st.write('Please upload your data to continue')
        log_action("Prompted user to upload data")
        update_log_in_db()
        
    else:
        # Allow user to select which file to view
        file_names = list(st.session_state.uploaded_files.keys())
        selected_file = st.selectbox("Select a file to view charts", file_names)

        if selected_file:
            processed_data = st.session_state.uploaded_files[selected_file]['processed']
            if processed_data is not None:
                df = pd.DataFrame(processed_data)
                st.session_state.parsed_df = df

                if st.session_state.log_id is not None:
                    st.write("If you find a bug, please report it to the developer with the " + f"Log ID: {st.session_state.log_id}")

                # Display the dataframe
                st.markdown("### Parsed Data")
                st.dataframe(dataframe_explorer(df, case=False), use_container_width=True)

                # Check if the DataFrame has the necessary columns
                required_columns = ['Date', 'Balance', 'Amount', 'Category', 'crdr']
                if all(column in df.columns for column in required_columns):
                    # Plotting the data
                    st.markdown("### Charts and Graphs")

                    try:
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

                        log_action("Displayed charts for selected file", details={'file_name': selected_file})
                        update_log_in_db()
                    except Exception as e:
                        st.error(f"Error displaying charts: {e}")
                        log_error(f"Error displaying charts: {e}", details={'file_name': selected_file})
                        update_log_in_db()
                else:
                    st.error("The uploaded file does not contain the necessary columns. Please upload a valid file.")
                    log_error("Uploaded file missing necessary columns", details={'file_name': selected_file})
                    update_log_in_db()
            else:
                st.error("Processed data not found. Please upload your data to continue.")
                log_error("Processed data not found", details={'file_name': selected_file})
                update_log_in_db()

# Run the main function
if __name__ == "__main__":
    show_charts()