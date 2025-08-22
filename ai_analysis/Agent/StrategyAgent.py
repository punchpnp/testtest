
from .Agent import BaseAgent, AgentResult

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate


class StrategyAgent(BaseAgent):
    name = "Strategy Agent"
    role = "Financial Strategist"
    
    def __init__(self, api_key: str):
        super().__init__()
        self.llm = ChatOpenAI(
          model="gpt-4o-2024-05-13",
          temperature=0.3,
          openai_api_key=api_key
        )
        self.prompt_template = PromptTemplate(
          template = self._get_template(),
          input_variables=["company_data"]
        )

    def _get_template(self):
        return """
        You are the Strategy Department for a financial group conducting M&A (mergers and acquisitions). Your task is to analyze the strategic profile of a proposed merger between an merging company and a target company.

You will be given structured information about both companies, including strategic goals, operational constraints, financial preferences, and integration capabilities.

Your objectives are:
- Assess strategic fit between the merger and the target.
- Identify realistic and high-impact synergy opportunities.
- Highlight key risks and sensitivities that may affect integration or value capture.
- Provide integration readiness considerations.
- Recommend valuation guidance and due diligence focus areas to downstream teams.

Be objective and industry-agnostic — your role is to support general M&A execution, not favor a specific company.

---

Company Data:
{company_data}

### ✅ Output Specification

Always output a structured JSON object using the following format:

```json
{{
  "strategicSummary": {{
    "fitAssessment": "Summarize strategic alignment, market fit, and cultural compatibility.",
    "synergyPotential": [
      "List specific synergies (e.g., cross-sell, shared infrastructure, IP leverage)."
    ],
    "strategicRisks": [
      "List key risks that may impact integration, brand value, or long-term sustainability."
    ],
    "integrationConsiderations": {{
      "requiresFounderBuyIn": true,
      "maxStoreExpansionFit": "E.g., 25 new points of sale over 2 years",
      "integrationDifficulty": "Low / Moderate / High",
      "culturalFit": "Low / Medium / High — with explanation"
    }}
  }},
  "valuationGuidance": {{
    "adjustedEBITDA": "Numeric value with unit",
    "valuationMultipleSuggested": "Numeric x",
    "impliedValuationRange": {{
      "low": "Low estimate with currency",
      "high": "High estimate with currency"
    }},
    "leverageAssumption": "Debt/EBITDA ratio used for modeling",
    "dealStructurePreferred": "Describe preferred structure (e.g., majority buyout + earn-out)",
    "sensitivityNotes": [
      "Describe any red flags that should trigger valuation adjustment"
    ]
  }},
  "dueDiligenceDirectives": {{
    "priorityAreas": [
      "Key contracts, assets, governance, or operational items to validate early"
    ],
    "riskAlerts": [
      {{
        "area": "Risk domain (e.g., IP, lease)",
        "note": "Specific issue and impact"
      }}
    ],
    "recommendedActions": [
      "Clear actions for DD, legal, and strategy teams to follow"
    ]
  }},
  "statusRecommendation": {{
    "nextStep": "Recommended next stage (e.g., proceed to valuation, hold, reject)",
    "confidenceScore": 1–10,
    "confidenceScoreReason": "Explain what drives this confidence rating (e.g., clarity of fit, data completeness, alignment)",
    "internalAlignment": "High / Medium / Low — with reasoning"
  }}
}}
    """

    #json_input: company information (merger+target)
    def run(self, json_input: str) -> AgentResult:
        # Implement the logic for the strategy agent to run on the DataFrame

        final_prompt = self.prompt_template.format(company_data=json_input)
        response = self.llm.invoke(final_prompt)
        
        return AgentResult(
            title="Strategy Analysis",
            content=response.content,
            data={
                "input": json_input,
                "metadata": response.response_metadata
            }
        )