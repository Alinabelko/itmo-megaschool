from pydantic import BaseModel
from typing import List, Dict, Any

class LLMAnswer(BaseModel):
    answer: int
    reasoning: str

class AgentState(BaseModel):
    messages: List[Dict[str, str]]
    current_step: str
    scraping_results: List[str] = []
    search_results: List[str] = []
    llm_answer: LLMAnswer | None = None 