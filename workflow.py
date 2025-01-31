from typing import Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from schemas.models import AgentState, LLMAnswer
from agents.synthesizer_agent import SynthesizerAgent
from agents.search_agent import SearchAgent
from agents.news_agent import NewsAgent
from agents.query_extractor_agent import QueryExtractorAgent
import logging
import asyncio

logger = logging.getLogger(__name__)

def create_workflow(
    synthesizer_agent: SynthesizerAgent, 
    search_agent: SearchAgent, 
    news_agent: NewsAgent,
    query_extractor_agent: QueryExtractorAgent
) -> StateGraph:
    workflow = StateGraph(AgentState)
    
    async def extract_query(state: AgentState) -> AgentState:
        state_dict = state.model_dump()
        result = await query_extractor_agent.run(state_dict)
        return AgentState(**result)
    
    async def search(state: AgentState) -> AgentState:
        state_dict = state.model_dump()
        search_query_state = {
            **state_dict,
            "messages": [{"role": "user", "content": state_dict["search_query"]}]
        }
        
        # Запускаем поиск параллельно
        search_task = search_agent.run(search_query_state)
        news_task = news_agent.run(search_query_state)
        
        # Ждем выполнения обоих запросов
        search_result, news_result = await asyncio.gather(search_task, news_task)
        
        combined_state = {
            **state_dict,
            "search_results": search_result["search_results"] + [
                {
                    "title": news["title"],
                    "content": news["content"],
                    "url": news["url"]
                }
                for news in news_result["scraping_results"]
            ]
        }
        
        return AgentState(**combined_state)
    
    async def synthesize(state: AgentState) -> AgentState:
        state_dict = state.model_dump()
        
        logger.info(f"State before synthesis: {state_dict}")
        search_context = "\nРезультаты поиска:\n"
        if state_dict.get("search_results"):
            for result in state_dict["search_results"]:
                search_context += f"\nИсточник: {result['title']}\nОписание: {result['content']}\nСсылка: {result['url']}\n"
        
        if state_dict["messages"]:
            user_query = state_dict["messages"][-1]["content"]
            state_dict["messages"][-1]["content"] = f"{user_query}\n\nКонтекст:\n{search_context}"
        
        result = await synthesizer_agent.run(state_dict)
        return AgentState(**result)
    
    # Добавляем узлы
    workflow.add_node("extract_query", extract_query)
    workflow.add_node("search", search)
    workflow.add_node("synthesize", synthesize)
    
    # Устанавливаем точку входа
    workflow.set_entry_point("extract_query")
    
    # Добавляем рёбра
    workflow.add_edge("extract_query", "search")
    workflow.add_edge("search", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()