import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_option_menu import option_menu
import openpyxl
import base64

# Check if Session State has uploaded files
if 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
    # Ask user to upload data and go through the steps
    st.write('Please upload your data to continue')
    
    # Button to redirect to Upload data page
    if st.button('Upload Data'):
        st.switch_page("pages/1_Upload Data.py")
else:
    # Allow user to select which file to view
    file_names = list(st.session_state.uploaded_files.keys())
    selected_file = st.selectbox("Select a file to view charts", file_names)

    if selected_file:
        df = st.session_state.uploaded_files[selected_file]
        st.session_state.parsed_df = df

        if st.session_state.log_id is not None:
            st.write("If you find a bug, please report it to the developer with the " + f"Log ID: {st.session_state.log_id}")

        # Display the dataframe
        st.markdown("### Parsed Data")
        st.dataframe(dataframe_explorer(df, case=False), use_container_width=True)

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
    else:
        st.error("Parsed data not found. Please upload your data to continue.")