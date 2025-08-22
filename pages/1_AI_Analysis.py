import os
import re
import time
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
import json


from ai_analysis import generate_report
from ai_analysis.Agent.MarkdownAgent import HTMLAgent
from ai_analysis.Agent.CompanyInformationAgent import CompanyInformationAgent
from ai_analysis.Agent.StrategyAgent import StrategyAgent
from ai_analysis.Agent.ValuationAgent import ValuationAgent
from ai_analysis.Agent.DueDiligenceAgent import DueDiligenceAgent
from ai_analysis.filechecker import company_file_exists
from ai_visualization.chart_generator import get_charts_analysis, get_charts_fig, read_charts, render_charts
from ai_visualization.data_loader import load_company_data
from ai_visualization.llm_agent import analyze_two_companies

# load_dotenv()

api_key = os.getenv("OPEN_API_KEY")





st.set_page_config(
    page_title="AI-Powered Company Financial Dashboard", 
    layout="wide"
    )

st.title("📊 Data Dashboard")
st.subheader("AI M&A Analysis")
st.write("Ask AI to do a pre-screening report on target company.")


#stage default:
def reset_flow():
    st.session_state.stage = "input"

def ensure_keys():
    st.session_state.setdefault("stage", "input")
    st.session_state.setdefault("co1", "Centel")
    st.session_state.setdefault("co2", "iberry")
    st.session_state.setdefault("co1_info", "")
    st.session_state.setdefault("co2_info", "")

if "stage" not in st.session_state:
    reset_flow()  
ensure_keys()

AGENT_REGISTRY = {
    "company_info_buyer": CompanyInformationAgent(api_key, "buyer"),
    "company_info_target": CompanyInformationAgent(api_key, "target"),
    "strategy": StrategyAgent(api_key),
    "valuation": ValuationAgent(api_key),
    "due_diligence": DueDiligenceAgent(api_key),
    "formatter": HTMLAgent(api_key)
}
def clean_json_output(llm_output: str):
    cleaned = re.sub(r"^```(?:json)?|```$", "", llm_output.strip(), flags=re.MULTILINE)
    return cleaned.strip()


#stage: user input
if st.session_state.stage =="input":
    with st.container(border=True):
        st.subheader("Choose Companies")
        c1,c2,c3 = st.columns([3,3,1])
        with c1:
            company_1 = st.text_input("Enter first company name", key="co1")
        with c2:
            company_2 = st.text_input("Enter second company name", key="co2")
        with c3:
            st.write("")
            st.write("")
            company_clicked = st.button("Compare", use_container_width=True)
        st.write("Optional:")
        with st.expander("Additional Information"):
            company_1_info = st.text_area("Enter additional information for " + company_1, height=100, key="co1_info")
            company_2_info = st.text_area("Enter additional information for " + company_2, height=100, key="co2_info")
    if company_clicked:
        co1 = st.session_state.get("co1", "").strip()
        co2 = st.session_state.get("co2", "").strip()
        co1_info = st.session_state.get("co1_info", "").strip()
        co2_info = st.session_state.get("co2_info", "").strip()

        if not co1 or not co2:
            st.error("Please enter both company names.")
        else:
            st.session_state.stage = "running"
            st.rerun()
            
#stage: running
if st.session_state.stage == "running":
    
    co1 = st.session_state.get("co1", "")
    co2 = st.session_state.get("co2", "")
    co1_info = st.session_state.get("co1_info", "")
    co2_info = st.session_state.get("co2_info", "")

    placeholder = st.empty()  # Placeholder for status messages
    #run agent
    with placeholder.container():
        stage1 = st.status("Getting company information...", expanded=True)
        # time.sleep(0.2)
        with stage1:
            #generate company information:

            co1_answer = AGENT_REGISTRY["company_info_buyer"].run({
                "company_name": co1,
                "company_description": co1_info
            })

            co2_answer = AGENT_REGISTRY["company_info_target"].run({
                "company_name": co2,    
                "company_description": co2_info
            })
            
            

            st.session_state.co1_info = clean_json_output(co1_answer.content)
            st.session_state.co2_info = clean_json_output(co2_answer.content)
            stage1.success("Company information retrieved successfully!")
            # st.chat_message("Company Information").text("Company information generated successfully!")

            # st.chat_message("Company Information").json(json1)
            # st.chat_message("Company Information").json(json2)
        stage2 = st.status("Running Strategy Agent...", expanded=True)
        # time.sleep(0.2)
        with stage2:
            #generate strategy information:
            co1_answer = st.session_state.co1_info
            co2_answer = st.session_state.co2_info

            input_data = {
                "buyer": json.loads(co1_answer),
                "target": json.loads(co2_answer)
            }
            input_data = json.dumps(input_data, indent=2)
            strategy_answer = AGENT_REGISTRY["strategy"].run(input_data)
            st.session_state.strategy_info = clean_json_output(strategy_answer.content)
            stage2.success("Strategy information retrieved successfully!")
            
        
            # st.chat_message("Strategy Information").markdown(strategy_answer.content)
            
        stage3 = st.status("Running Valuation Agent...", expanded=True)
        with stage3:
            input_data = {
                "strategy": st.session_state.strategy_info,
                "company_data": input_data
            }
            valuation_answer = AGENT_REGISTRY["valuation"].run(input_data)
            st.session_state.valuation_info = clean_json_output(valuation_answer.content)
            stage3.success("Valuation information retrieved successfully!")

            # st.chat_message("Valuation Information").markdown(valuation_answer.content)
        if (company_file_exists(co1) and company_file_exists(co2)):
            stage_ex1 = st.status("Found company financial reports in database, Creating chart...")
            with stage_ex1:
                # Create the chart using the financial reports
                df1 = load_company_data(co1) 
                df2 = load_company_data(co2)
                df1["Company"] = co1
                df2["Company"] = co2
                combined_df = pd.concat([df1, df2])
                chart_plan = analyze_two_companies([co1, co2], combined_df)
                st.session_state.chart_plan = chart_plan
                st.session_state.df = combined_df

                stage_ex1.success("Chart created successfully!")
        else:
            st.session_state.chart_plan = "[]"
            st.session_state.df = pd.DataFrame()
            
            stage_ex1 = st.status("No company financial reports found in database. Skipping chart creation.")

        stage4 = st.status("Running Due Diligence Agent...", expanded=True)
        with stage4:
            # Run the due diligence agent
            input_data["valuation"] = st.session_state.valuation_info
            
            due_diligence_answer = AGENT_REGISTRY["due_diligence"].run(input_data)

            stage4.success("Due Diligence analysis completed successfully!")
            st.session_state.due_diligence_info = clean_json_output(due_diligence_answer.content)

            st.session_state.stage = "result"
            st.rerun()

if st.session_state.stage == "result":
    st.success("Analysis completed successfully!")
    progress_bar = st.progress(0, text="Generating final report...")
    with st.spinner(f"{st.session_state.co1} information..."):
        company_1_html = AGENT_REGISTRY["formatter"].run(st.session_state.co1_info)
    with st.spinner(f"{st.session_state.co2} information..."):
        progress_bar.progress(20, text="Generating final report...")
        company_2_html = AGENT_REGISTRY["formatter"].run(st.session_state.co2_info)
    with st.spinner("Generating Strategy report..."):
        progress_bar.progress(40, text="Generating final report...")
        strategy_html = AGENT_REGISTRY["formatter"].run(st.session_state.strategy_info)
    with st.spinner("Generating Valuation report..."):
        progress_bar.progress(60, text="Generating final report...")
        valuation_html = AGENT_REGISTRY["formatter"].run(st.session_state.valuation_info)
    with st.spinner("Generating Due Diligence report..."):
        progress_bar.progress(80, text="Generating final report...")
        due_diligence_html = AGENT_REGISTRY["formatter"].run(st.session_state.due_diligence_info)
    with st.spinner("Getting pdf ready..."):
        progress_bar.progress(95, text="Generating final report...")
         #for download:
        charts_arr = read_charts(st.session_state.chart_plan)
        chart_fig_arr = get_charts_fig(charts_arr, st.session_state.df)
        chart_fig_analysis = get_charts_analysis(charts_arr)
        
        report= generate_report.ReportGenerator(
            co1=company_1_html.content,
            co2=company_2_html.content,
            strat=strategy_html.content,
            var=valuation_html.content,
            chart=chart_fig_arr,
            chart_analysis=chart_fig_analysis,
            due=due_diligence_html.content
        )
        
        

    progress_bar.empty()
        # Here you would generate the report based on the analysis

    st.html(company_1_html.content)
    st.html(company_2_html.content)
    st.html(strategy_html.content)
    st.html(valuation_html.content)
    if st.session_state.chart_plan != "[]":
        render_charts(st.session_state.chart_plan, st.session_state.df)
        st.write(chart_fig_analysis)
    st.html(due_diligence_html.content)


    pdf_file = report.to_pdf()
    with st.spinner("Generating PDF..."):
        st.download_button(
            label="📥 Download Full Report as PDF",
            data=report.to_pdf(),
            file_name="report.pdf",
            mime="application/pdf"
        )



def display_html(content):
    header = """
    
    """
    st.html(content)