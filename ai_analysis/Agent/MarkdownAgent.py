import re
from .Agent import BaseAgent, AgentResult

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class HTMLAgent(BaseAgent):
    name = "HTML Agent"
    role = "HTML Formatter"

    def __init__(self, api_key: str):
        super().__init__()
        self.llm = ChatOpenAI(
            model="gpt-4o-2024-05-13",
            temperature=0.2,
            openai_api_key=api_key
        )
        self.prompt_template = PromptTemplate(
            template=self._get_template(),
            input_variables=["content"]
        )

    def _get_template(self):
        return """
You are a HTML formatter. Your job is to take the input content and format it as HTML.
            
Your task is to translate the following JSON into a clean, professional, and well-structured HTML document. Do **not** include any styling or `<style>` tags — just semantic HTML structure using tags like `<h1>`, `<h2>`, `<h3>`, `<p>`, `<ul>`, `<li>`, and `<table>`. this is a part of larger HTML document, you would not need to generate <html> or <body>.

Instructions:

1. Start with a main `<h1>` title
2. Group each top-level concept clearly under `<h2>` or `<h3>` headings.
3. Use paragraphs `<p>` for prose and bullet points `<ul><li>` for lists.
4. Convert arrays like `synergyPotential`, `riskAlerts`, or `recommendedActions` into bullet lists or tables where appropriate.
5. Use `<table>` only if the content is best understood in rows (e.g., risk alerts with `area` and `note`).
6. This part of document will be used as an header for the main document so you should cut down irrelevant information that the viewer doesn't need to see accordingly. focus on just provide enough context for strategy and valuation that will be provided down the line.
7. This document will be use to be read by non-technical person. Do not use any `<pre>` or `<code>` tags.
Here is the JSON input:
    {content}
        """
        
    def run(self, json_input: str) -> AgentResult:
        final_prompt = self.prompt_template.format(
            content=json_input)
        response = self.llm.invoke(final_prompt)
        
        return AgentResult(
            title="HTML Report",
            content=self.cleanOutput(response.content),
            data={
                "input": json_input,
                "metadata": response.response_metadata
            }
        )
        
    def cleanOutput(self, content: str):
        cleaned = re.sub(r"^```(?:html)?|```$", "", content.strip(), flags=re.MULTILINE)
        return cleaned.strip()