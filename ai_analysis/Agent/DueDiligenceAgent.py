from .Agent import BaseAgent, AgentResult

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class DueDiligenceAgent(BaseAgent):
    name = "Due Diligence Agent"
    role = "Due Diligence Specialist"

    def __init__(self, api_key: str):
        super().__init__()
        self.llm = ChatOpenAI(
            model="gpt-4o-2024-05-13",
            temperature=0.2,
            openai_api_key=api_key
        )
        self.prompt_template = PromptTemplate(
            template=self._get_template(),
            input_variables=["company_data", "strategy", "valuation"]
        )

    def _get_template(self):
        return """
You are given the target company's full strategic and financial assessment.

Your task is to extract key due diligence directives based on the following:
- Company Data: {company_data}
- Strategy: {strategy}
- Valuation: {valuation}

Your response should include specific due diligence questions or areas of concern related to each of these aspects.
You are the Due Diligence Department for a financial group executing M&A transactions. Your job is to produce a clear, prioritized checklist of due diligence requirements based on:

- Strategic fit and risks
- Valuation assumptions
- Deal structure
- Operational model
- Financials, assets, and ownership

You must:
1. Identify critical documents and contracts to validate.
2. Flag specific risks requiring early legal, operational, or financial review.
3. Recommend focused actions for legal, financial, and operational DD teams.
4. Return your response in structured JSON format, usable by downstream agents and investment committee systems.

        
    """

    def run(self, json_input: dict) -> AgentResult:
        
        final_prompt = self.prompt_template.format(
            strategy=json_input["strategy"],
            company_data=json_input["company_data"],
            valuation=json_input["valuation"]
        )
        response = self.llm.invoke(final_prompt)
        
        return AgentResult(
            title="Due Diligence Report",
            content=response.content,
            data={
                "input": json_input,
                "metadata": response.response_metadata
            }
        )