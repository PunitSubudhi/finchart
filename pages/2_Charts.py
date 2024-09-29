import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_option_menu import option_menu
import openpyxl
import base64



# Check if Session State has parsed_df
if 'parsed_df' not in st.session_state:
    # Ask user to upload data and go through the steps
    st.write('Please upload your data to continue')
    
    #button to redirect to Upload data page
    if st.button('Upload Data'):
        st.switch_page("pages/1_Upload Data.py")

# Ensure parsed_df is available
if 'parsed_df' in st.session_state and st.session_state.parsed_df is not None:
    
    if st.session_state.log_id is not None:
        st.write("If you find a bug, please report it to the developer with the " + f"Log ID: {st.session_state.log_id}")
    
    df = st.session_state.parsed_df
    
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