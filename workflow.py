from typing import Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from schemas.models import AgentState, LLMAnswer
from agents.synthesizer_agent import SynthesizerAgent
from agents.search_agent import SearchAgent
import logging

logger = logging.getLogger(__name__)

def create_workflow(synthesizer_agent: SynthesizerAgent, search_agent: SearchAgent) -> StateGraph:
    workflow = StateGraph(AgentState)
    
    async def search(state: AgentState) -> AgentState:
        # Преобразуем состояние в словарь для агента
        state_dict = state.model_dump()
        
        result = await search_agent.run(state_dict)
        
        return AgentState(**result)
    
    async def synthesize(state: AgentState) -> AgentState:
        state_dict = state.model_dump()
        
        logger.info(f"State before synthesis: {state_dict}")
        search_context = "\nРезультаты поиска:\n"
        if state_dict.get("search_results"):
            for result in state_dict["search_results"]:
                search_context += f"\nИсточник: {result['title']}\nОписание: {result['snippet']}\nСсылка: {result['url']}\n"
        
        if state_dict["messages"]:
            user_query = state_dict["messages"][-1]["content"]
            state_dict["messages"][-1]["content"] = f"{user_query}\n\nКонтекст:\n{search_context}"
        
        logger.info(f"Modified query with context: {state_dict['messages'][-1]['content']}")
        
        result = await synthesizer_agent.run(state_dict)
        
        return AgentState(**result)
    
    workflow.add_node("search", search)
    workflow.add_node("synthesize", synthesize)
    
    workflow.set_entry_point("search")
    workflow.add_edge("search", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()