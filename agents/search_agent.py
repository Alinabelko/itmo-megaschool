from typing import Dict, Any, List
import trafilatura
import httpx
from urllib.parse import urlparse

from utils.logger import setup_logger
from .base import BaseAgent
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import BaseMessage

logger = setup_logger()

class SearchAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm)
        self.search_tool = DuckDuckGoSearchResults(max_results=3)
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def fetch_full_text(self, url: str) -> str:
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            logger.info(f"Получен ответ c {url}: {response.text}")
            
            # Извлекаем текст с помощью trafilatura
            downloaded = trafilatura.extract(
                response.text,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            
            return downloaded or ""
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return ""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = state["messages"][-1]["content"]
            # Добавляем ИТМО к запросу для получения релевантных результатов
            formatted_query = f"{query} ИТМО site:itmo.ru OR site:news.itmo.ru"
            
            logger.info(f"Searching with query: {formatted_query}")
            
            search_results = await self.search_tool.ainvoke(formatted_query)
            logger.info(f"Raw search results: {search_results}")
            
            # Парсим результаты поиска
            formatted_results = []
            if isinstance(search_results, str):
                parts = search_results.split(", ")
                current_result = {}
                for part in parts:
                    if len(formatted_results) >= 3:
                        break
                    if ": " in part:
                        key, value = part.split(": ", 1)
                        if key in ["snippet", "title", "link"]:
                            current_result[key] = value.strip()
                            if len(current_result) == 3:
                                # Получаем полный текст для каждого результата
                                full_text = await self.fetch_full_text(current_result["link"])
                                if full_text:  # Добавляем только если удалось получить текст
                                    formatted_results.append({
                                        "title": current_result.get("title", ""),
                                        "url": current_result.get("link", ""),
                                        "content": full_text
                                    })
                                current_result = {}
            
            # Обрезаем результаты до 3, если каким-то образом получили больше
            formatted_results = formatted_results[:3]
            
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

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose() 