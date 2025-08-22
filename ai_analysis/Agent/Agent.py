import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import pandas as pd

api_key = os.getenv("OPEN_API_KEY")

class AgentResult:
    def __init__(self, title: str, content: str, data: dict | None = None):
        self.title = title
        self.content = content
        self.data = data or {}
        
class BaseAgent:
    name = "Agent"
    role = ""
    def run(self, json_input: str) -> AgentResult:
        # Implement the logic for the agent to run on the DataFrame
        pass
    
