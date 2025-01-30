from typing import Dict, Any
from .base import BaseAgent
from langchain_core.messages import SystemMessage, HumanMessage

class SynthesizerAgent(BaseAgent):
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Получаем запрос пользователя
            user_query = state["messages"][-1]["content"]
            
            # Создаем системный промпт
            system_prompt = """Ты - ассистент Университета ИТМО. Твоя задача - предоставлять точную и полезную 
            информацию об университете. Используй формальный, но дружелюбный стиль общения. Отвечай на русском языке."""
            
            # Формируем сообщения для модели
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]
            
            # Получаем ответ от модели
            response = self.llm.invoke(messages)
            
            return {
                **state,
                "final_response": response.content
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Ошибка синтеза ответа: {str(e)}",
                "final_response": "Извините, произошла ошибка при обработке вашего запроса."
            } 