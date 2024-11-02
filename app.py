import streamlit as st
import pandas as pd
import numpy as np
from custom_functions import *


if 'log' not in st.session_state:
    initialize_log()

st.title('Welcome to FinChart | A financial charting app')

st.switch_page("pages/3_login.py")