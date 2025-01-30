from typing import TypedDict, Annotated, Sequence
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    current_step: str
    scraping_results: list
    search_results: list
    final_response: str

class BaseAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm 