from typing import Dict, Any, List

from utils.logger import setup_logger
from .base import BaseAgent
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import BaseMessage

logger = setup_logger()

class SearchAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm)
        self.search_tool = DuckDuckGoSearchResults(max_results=3)

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = state["messages"][-1]["content"]
            # Добавляем ИТМО к запросу для получения релевантных результатов
            formatted_query = f"{query} ИТМО site:itmo.ru OR site:news.itmo.ru"
            
            logger.info(f"Searching with query: {formatted_query}")
            
            search_results = await self.search_tool.ainvoke(formatted_query)
            logger.info(f"Raw search results: {search_results}")
            
            # Парсим строку результатов
            # Результаты приходят в формате "snippet: ..., title: ..., link: ..."
            formatted_results = []
            if isinstance(search_results, str):
                parts = search_results.split(", ")
                current_result = {}
                for part in parts:
                    if ": " in part:
                        key, value = part.split(": ", 1)
                        if key in ["snippet", "title", "link"]:
                            current_result[key] = value
                            if len(current_result) == 3:  # Если собрали все поля
                                formatted_results.append({
                                    "title": current_result.get("title", ""),
                                    "url": current_result.get("link", ""),
                                    "snippet": current_result.get("snippet", "")
                                })
                                current_result = {}
            
            logger.info(f"Formatted search results: {formatted_results}")

            new_state = {
                **state,
                "search_results": formatted_results,
                "current_step": "search"
            }
            
            logger.info(f"New state after search: {new_state}")
            return new_state
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return {
                **state,
                "error": f"Ошибка поиска: {str(e)}",
                "search_results": []
            } 