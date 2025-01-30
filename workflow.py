from typing import Dict, Any, Annotated
from langgraph.graph import StateGraph
from agents.base import AgentState
from agents.search_agent import SearchAgent
from agents.scraping_agent import ScrapingAgent
from agents.synthesizer_agent import SynthesizerAgent

def create_workflow(
    search_agent: SearchAgent,
    scraping_agent: ScrapingAgent,
    synthesizer_agent: SynthesizerAgent
) -> StateGraph:
    
    workflow = StateGraph(AgentState)
    
    def router(state: AgentState) -> str:
        if not state["search_results"]:
            return "search"
        elif not state["scraping_results"]:
            return "scrape"
        else:
            return "synthesize"
    workflow.add_node("search", search_agent.run)
    workflow.add_node("scrape", scraping_agent.run)
    workflow.add_node("synthesize", synthesizer_agent.run)
    
    workflow.set_entry_point("router")
    workflow.add_router("router", router)
    
    workflow.add_edge("search", "router")
    workflow.add_edge("scrape", "router")
    workflow.add_edge("synthesize", "end")
    
    return workflow.compile() 