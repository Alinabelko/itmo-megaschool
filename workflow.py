from typing import Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from agents.base import AgentState
from agents.synthesizer_agent import SynthesizerAgent

def create_workflow(synthesizer_agent: SynthesizerAgent) -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Добавляем только узел синтезатора
    workflow.add_node("synthesize", synthesizer_agent.run)
    

    workflow.set_entry_point("synthesize")
    
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()