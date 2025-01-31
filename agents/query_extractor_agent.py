from typing import Dict, Any
from .base import BaseAgent
from utils.logger import setup_logger

logger = setup_logger()

class QueryExtractorAgent(BaseAgent):
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            messages = [
                {"role": "system", "content": """
                Ты - агент, который анализирует вопрос и выделяет из него ключевые слова для поиска.
                Выдели самую важную часть вопроса, которая подходит для поиска информации.
                Не включай варианты ответов в поисковую фразу.
                Ответ должен быть краток и содержать только поисковую фразу.

                Пример:
                Вопрос: В каком рейтинге (по состоянию на 2021 год) ИТМО впервые вошёл в топ-400 мировых университетов?
                1. ARWU
                2. Times Higher Education 
                3. QS World University Rankings
                4. U.S. News
                
                Поисковая фраза: ИТМО топ-400
                """},
                {"role": "user", "content": state["messages"][-1]["content"]}
            ]

            response = await self.llm.ainvoke(messages)
            search_query = response.content

            logger.info(f"Extracted search query: {search_query}")
            
            return {
                **state,
                "search_query": search_query
            }
            
        except Exception as e:
            logger.error(f"Ошибка в QueryExtractorAgent: {str(e)}", exc_info=True)
            return {
                **state,
                "search_query": state["messages"][-1]["content"]
            } 