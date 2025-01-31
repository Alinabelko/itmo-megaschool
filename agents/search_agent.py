from typing import Dict, Any, List
import trafilatura
import httpx
from urllib.parse import urlparse
import asyncio

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
            formatted_query = f"{query} ИТМО site:itmo.ru OR site:news.itmo.ru"
            
            logger.info(f"Searching with query: {formatted_query}")
            
            search_results = await self.search_tool.ainvoke(formatted_query)
            logger.info(f"Raw search results: {search_results}")
            
            # Парсим результаты поиска
            urls_to_fetch = []
            current_result = {}
            if isinstance(search_results, str):
                parts = search_results.split(", ")
                for part in parts:
                    if len(urls_to_fetch) >= 3:
                        break
                    if ": " in part:
                        key, value = part.split(": ", 1)
                        if key in ["snippet", "title", "link"]:
                            current_result[key] = value.strip()
                            if len(current_result) == 3:
                                urls_to_fetch.append(current_result)
                                current_result = {}

            # Параллельный скраппинг всех URL
            fetch_tasks = [
                self.fetch_full_text(result["link"]) 
                for result in urls_to_fetch
            ]
            full_texts = await asyncio.gather(*fetch_tasks)
            
            # Формируем результаты
            formatted_results = [
                {
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "content": content
                }
                for result, content in zip(urls_to_fetch, full_texts)
                if content  # Добавляем только если удалось получить текст
            ]
            
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