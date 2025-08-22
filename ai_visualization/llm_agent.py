from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

import os

api_key = os.getenv("OPEN_API_KEY")

llm = ChatOpenAI(model="gpt-4o-2024-05-13", temperature=0, openai_api_key=api_key)

template = """
You are a financial analyst. Analyze the following dataset for {company}:

{data}

Suggest a set of visualizations that would best represent the data.
Return your answer in JSON with this format, this format must be loadable by jsonloader:
[
  {{"type": "line", "title": "Revenue over Time", "x": "Date", "y": "Revenue", "filter": "Gross Profit"}},
  {{"type": "bar", "title": "Total Revenue Share", "x": "Company", "values": "Amount", "filter": "Operating Profit (EBITDA)"}},
  {{"type": "analysis", "title": "Overall Analysis", "value": "Provide a summary of the financial performance of {company}."}}
]
"""

prompt = PromptTemplate(
    input_variables=["company", "data"],
    template=template
)

def analyze_two_companies(company_names, df):
    # Convert DataFrame to CSV for AI context
    csv_sample = df.head(50).to_csv(index=False)  
    df_summary = summarize_df(df)

    prompt = f"""
You are a financial analyst. Analyze the following dataset for {company_names[0]} and {company_names[1]}:

{df_summary}

You are a data visualization expert.
We have data from TWO companies: {company_names[0]} and {company_names[1]}.
The column 'Company' identifies which row belongs to which company.
Generate JSON describing charts that COMPARE these two companies in the same figure where possible.

Suggest a set of visualizations that would best represent the data.


Rules:
- Prefer multi-series line charts for time series (x-axis: Date, y-axis: metric)
- For bar charts, use grouped bars by Company
- Output ONLY valid JSON array, without code fences or extra text
- Each chart JSON must include: type, title, x, y, filter.
- Give atleast 5 different charts if possible, Try to use as many different chart types as you can.
- Always include summary analysis in the form of {{type: "analysis", title: "<title>", value: "<summary>"}} at the end
- Pick x, y axis and filter from the dataset columns, do not create new columns.
- Bar Chart should specify a specific year after 2018, also try to pick X axis that is both relevant to both companies.

Here is the summary of dataset:
{df_summary}
Here is a sample of the combined dataset:
{csv_sample}
"""

    response = llm.invoke(prompt)  # Your LangChain/OpenAI call
    return response.content



def summarize_df(df):
    summary = {
        "columns": list(df.columns),
        "num_rows": len(df),
        "sample_rows": df.head(10).to_dict(orient='records'),
        "desc": df.describe(include='all').to_dict(),
        "unique_categories": df['Subcategory'].unique().tolist(),
        "years": df['Year'].unique().tolist()
    }
    return summary