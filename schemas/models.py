from typing import Any, Dict, List

from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class LLMAnswer(BaseModel):
    answer: int | None
    reasoning: str

class AgentState(BaseModel):
    messages: List[Dict[str, str]]
    current_step: str
    search_query: str = ""
    scraping_results: List[Dict[str, str]] = []
    search_results: List[Dict[str, str]] = []
    llm_answer: LLMAnswer 