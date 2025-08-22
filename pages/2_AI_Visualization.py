import streamlit as st
import pandas as pd
from ai_visualization.data_loader import load_company_data
from ai_visualization.llm_agent import analyze_two_companies, summarize_df
from ai_visualization.chart_generator import render_charts


st.set_page_config(
    page_title="AI-Powered Company Financial Dashboard", 
    layout="wide")



st.title("📊 Data PoodPard")

st.subheader("AI Chart Visualization")
st.write("This is the AI chart visualization page.")
companies = ["Centel", "iberry"]
# Create two columns for side-by-side dropdowns
col1, col2 = st.columns(2)
with col1:
    company_1 = st.selectbox("Select first company", companies, key="company_1")
with col2:
    remaining_companies = [c for c in companies if c != company_1]
    company_2 = st.selectbox("Select second company", remaining_companies, key="company_2")


if company_1 and company_2 and st.button("Compare Companies"):
    status_placeholder = st.empty()  # placeholder to update messages dynamically

    with st.spinner("Loading company report..."):
        df1 = load_company_data(company_1)
        df2 = load_company_data(company_2)

        df1["Company"] = company_1
        df2["Company"] = company_2
        combined_df = pd.concat([df1, df2])
        

    
    with st.spinner("AI Agent Analyzing data..."):
        chart_plan = analyze_two_companies([company_1, company_2], combined_df)

    
    with st.spinner("Generating charts..."):
        with st.expander("View Chart Plan"):
            st.json(chart_plan)
        render_charts(chart_plan, combined_df)

    status_placeholder.success("✅ Report generated successfully!")
    combined_df_display = combined_df.head(100)
    st.write("### Combined Financial Data")
    with st.expander("View Combined Data"):
        st.dataframe(combined_df_display)
        st.json(summarize_df(combined_df))
