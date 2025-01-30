from typing import TypedDict, Annotated, Sequence
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from schemas.models import LLMAnswer

class AgentState(BaseModel):
    messages: List[Dict[str, str]]
    current_step: str
    scraping_results: List[str] = []
    search_results: List[str] = []
    llm_answer: LLMAnswer | None = None

class BaseAgent(ABC):
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm 

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass 