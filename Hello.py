import kaleido
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
# kaleido.get_chrome_sync()


st.set_page_config(
    page_title="AI-Powered Company Financial Dashboard", 
    layout="wide")



st.title("📊 Data Dashboard")

st.markdown(
    """
    ## Welcome to the AI-Powered Company Financial Dashboard!
    **👈 Select workflows from the sidebar on the left** to see some examples
    ### What our AI can currently do:
    - **AI Analysis**: Get insights and PDFs report from comparing two companies <-recommended
    - **AI Chart Visualization**: Visualize both companies' performance
"""
)
