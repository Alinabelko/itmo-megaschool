from typing import Dict, Any, List
from .base import BaseAgent
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import BaseMessage

class SearchAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm)
        self.search_tool = DuckDuckGoSearchResults(max_results=3)

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = state["messages"][-1]["content"]
            # Добавляем ИТМО к запросу для получения релевантных результатов
            formatted_query = f"{query} ИТМО site:itmo.ru OR site:news.itmo.ru"
            
            # Выполняем поиск
            search_results = self.search_tool.invoke(formatted_query)
            
            # Форматируем результаты
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })

            return {
                **state,
                "search_results": formatted_results
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Ошибка поиска: {str(e)}",
                "search_results": []
            } 