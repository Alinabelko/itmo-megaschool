from typing import Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from agents.models import AgentState, LLMAnswer
from agents.synthesizer_agent import SynthesizerAgent

def create_workflow(synthesizer_agent: SynthesizerAgent) -> StateGraph:
    workflow = StateGraph(AgentState)
    
    def run_synthesizer(state: AgentState) -> AgentState:
        # Преобразуем состояние в словарь для агента
        state_dict = state.model_dump()
        
        # Получаем обновленное состояние от агента
        result = synthesizer_agent.run(state_dict)
        
        # Создаем новый объект AgentState
        return AgentState(**result)
    
    # Добавляем узел синтезатора
    workflow.add_node("synthesize", run_synthesizer)
    
    # Устанавливаем начальную точку и конечный узел
    workflow.set_entry_point("synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()