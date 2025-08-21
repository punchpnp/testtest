import json
import re
import streamlit as st
import plotly.express as px

def clean_json_output(llm_output: str):
    cleaned = re.sub(r"^```(?:json)?|```$", "", llm_output.strip(), flags=re.MULTILINE)
    return cleaned.strip()

def read_charts(chart_json_str):
    try:
        charts = json.loads(clean_json_output(chart_json_str))
    except json.JSONDecodeError:
        st.error("AI returned invalid JSON")
        return []
    return charts

def create_chart_line(df, chart):
    scope = df[df["Subcategory"] == chart["filter"]['Subcategory']] 
    # st.write("Filtered data:", scope)  # Check filtered data

    fig = px.line(
        scope,
        x=chart["x"],
        y=chart["y"],
        color="Company",
        markers=True,
        title=chart["title"],
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    return fig
    #st.plotly_chart(fig, use_container_width=True)
    # if show_df:
    #     with st.expander(f"Filtered data for line chart: {chart['title']}"):
    #         st.write(scope)

    
def create_chart_bar(df, chart):
    scope = df
    if chart['filter'].get('Category'):
        scope = df[(df["Category"] == chart["filter"]['Category'])]
    if chart['filter'].get('Subcategory'):
        scope = df[(df["Subcategory"] == chart["filter"]['Subcategory'])]
    if chart["filter"].get('Year'):
        scope = scope[scope["Year"] == chart["filter"]['Year']]

    

    fig = px.bar(
        scope,
        x=chart["x"],
        y=chart["y"],
        barmode="group",
        color="Company",
        title=chart["title"],
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Plotly
    ).update_traces(width=0.3).update_layout(bargap=0.2, bargroupgap=0.1)
    return fig
    # st.plotly_chart(fig, use_container_width=True)
    # if show_df:
    #     with st.expander(f"Filtered data for bar chart: {chart['title']}"):
    #         st.write(scope)

def creat_chart_pie(df, chart):
    scope = df[df["Subcategory"] == chart["filter"]['Subcategory']]






def render_charts(chart_json_str, df, analysis=False):
    try:
        charts = json.loads(clean_json_output(chart_json_str))
    except json.JSONDecodeError:
        st.error("AI returned invalid JSON")
        return

    cols_per_row = 2
    rows = (len(charts) + 1) // cols_per_row

    for row_idx in range(rows):
        cols = st.columns(cols_per_row)
        for i, chart in enumerate(charts[row_idx*cols_per_row: (row_idx+1)*cols_per_row]):
            with cols[i]:
                color = "Company"
                if chart["type"] == "line":
                    fig = create_chart_line(df, chart)
                    st.plotly_chart(fig, use_container_width=True)
                    continue
                elif chart["type"] == "bar":
                    fig = create_chart_bar(df, chart)
                    st.plotly_chart(fig, use_container_width=True)
                    continue
                # elif chart["type"] == "pie":
                #     fig = px.pie(df, names=chart["names"], values=chart["values"], title=chart["title"], color=color)
                elif chart["type"] == "analysis":
                    if (analysis):
                        st.write(chart["title"])
                        st.write(chart["value"])
                    continue
                else:
                    st.error(f"Unsupported chart type: {chart['type']}")
                    continue
                st.plotly_chart(fig, use_container_width=True)


def get_charts_fig(charts_arr, df):
    fig_array = []

    for chart in charts_arr:
        if chart["type"] == "line":
            fig = create_chart_line(df, chart)
            fig_array.append(fig)
        elif chart["type"] == "bar":
            fig = create_chart_bar(df, chart)
            fig_array.append(fig)
        # elif chart["type"] == "pie":
        #     fig = create_chart_pie(df, chart)
        #     fig_array.append(fig)
        elif chart["type"] == "analysis":
            continue
        else:
            st.error(f"Unsupported chart type: {chart['type']}")

    return fig_array

def get_charts_analysis(chart_arr):
    for chart in chart_arr:
        if chart["type"] == "analysis":
            return chart["value"]