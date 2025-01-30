import json
from typing import Dict, Any

from utils.logger import setup_logger
from pydantic import BaseModel
from .base import BaseAgent
from ..schemas.models import LLMAnswer
from langchain_core.messages import SystemMessage, HumanMessage

logger = setup_logger()

class SynthesizerAgent(BaseAgent):  
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_query = state["messages"][-1]["content"]
            
            system_prompt = """Ты - ассистент Университета ИТМО. Твоя задача - предоставлять точную информацию об университете. 

            Формат ответа:
            - Строго используй JSON с двумя полями: 
            - `answer` (число): номер правильного варианта или 0, если ответ не найден
            - `reasoning` (строка): подробное объяснение на русском языке

            Пример:
            {"answer": 2, "reasoning": "Поступить можно через личный кабинет..."}

            Запрещено:
            - Добавлять текст вне JSON
            - Менять структуру ответа
            - Использовать Markdown-разметку
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]
            
            response = self.llm.invoke(messages, response_format={"type": "json_object"})
            logger.info(f"Raw LLM response: {response.content}")
            
            try:
                response_data = json.loads(response.content.strip())
                logger.info(f"Parsed response data: {response_data}")
                llm_answer = LLMAnswer(
                    answer=int(response_data.get("answer", 0)),
                    reasoning=response_data.get("reasoning", "Объяснение отсутствует")
                )
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Error parsing response: {e}")
                llm_answer = LLMAnswer(
                    answer=0,
                    reasoning=f"Ошибка обработки ответа: {str(e)}"
                )

            new_state = {
                **state,
                "llm_answer": llm_answer,
                "current_step": "synthesize"
            }
            logger.info(f"New state in synthesizer: {new_state}")
            return new_state
            
        except Exception as e:
            logger.error(f"Synthesizer error: {e}")
            llm_answer = LLMAnswer(
                answer=0,
                reasoning=f"Ошибка системы: {str(e)}"
            )
            return {
                **state,
                "llm_answer": llm_answer,
                "current_step": "synthesize"
            }