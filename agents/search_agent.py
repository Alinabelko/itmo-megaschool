from typing import Dict, Any, List
import trafilatura
import httpx
from urllib.parse import urlparse
import asyncio
from googleapiclient.discovery import build
from config import settings

from utils.logger import setup_logger
from .base import BaseAgent
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import BaseMessage

logger = setup_logger()

class SearchAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm)
        self.search_service = build(
            "customsearch", "v1", 
            developerKey=settings.GOOGLE_API_KEY
        )
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

    async def search_google(self, query: str) -> List[Dict]:
        try:
            results = self.search_service.cse().list(
                q=query,
                cx=settings.GOOGLE_CSE_ID,
                num=3
            ).execute()

            search_results = []
            for item in results.get('items', []):
                search_results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                })
            return search_results
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = state["messages"][-1]["content"]
            formatted_query = f"{query} ИТМО site:itmo.ru OR site:news.itmo.ru"
            
            logger.info(f"Searching with query: {formatted_query}")
            
            search_results = await self.search_google(formatted_query)
            logger.info(f"Raw search results: {search_results}")
            
            # Параллельный скраппинг всех URL
            fetch_tasks = [
                self.fetch_full_text(result["link"]) 
                for result in search_results
            ]
            full_texts = await asyncio.gather(*fetch_tasks)
            
            # Формируем результаты
            formatted_results = [
                {
                    "title": result["title"],
                    "url": result["link"],
                    "content": content
                }
                for result, content in zip(search_results, full_texts)
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