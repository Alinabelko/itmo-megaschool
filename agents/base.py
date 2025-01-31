from abc import ABC, abstractmethod
from typing import Annotated, Any, Dict, List, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import Graph, StateGraph
from pydantic import BaseModel

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