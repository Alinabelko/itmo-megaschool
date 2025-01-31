import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from schemas.models import LLMAnswer
from utils.logger import setup_logger

from .base import BaseAgent

logger = setup_logger()

class SynthesizerAgent(BaseAgent):  
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_query = state["messages"][-1]["content"]
            logger.info(f"User query for synthesizer: {user_query}")

            system_prompt = """Ты - ассистент Университета ИТМО. Твоя задача - предоставлять точную информацию об университете на основе результатов поиска. 

            Формат ответа:
            - Строго используй JSON с двумя полями: 
            - `answer` (число или null): 
                - номер правильного варианта (1-10)
                - null, если вопрос не предполагает выбор из вариантов
            - `reasoning` (строка): подробное объяснение на русском языке

            Структура вопроса:
            - Текстовое описание
            - Пронумерованные варианты ответов (1-10)
            - Варианты разделены переносом строки

            Пример:
            {"answer": 2, "reasoning": "Судя по информации с сайта, поступить можно через личный кабинет..."}
            {"answer": null, "reasoning": "Вопрос не предполагает выбор из вариантов..."}

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
                
                # Обработка answer с учетом возможного None
                answer_value = response_data.get("answer")
                answer = int(answer_value) if answer_value is not None else None
                
                llm_answer = LLMAnswer(
                    answer=answer,
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