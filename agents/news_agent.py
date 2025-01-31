from typing import Dict, Any
import aiohttp
from bs4 import BeautifulSoup
from .base import BaseAgent
from utils.logger import setup_logger

logger = setup_logger()

class NewsAgent(BaseAgent):
    async def _fetch_news_links(self, query: str) -> list[str]:
        logger.info(f"Начинаю поиск новостей по запросу: {query}")
        async with aiohttp.ClientSession() as session:
            search_url = f"https://news.itmo.ru/ru/search/?search={query}"
            async with session.get(search_url) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при поиске новостей: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                news_links = []
                
                # Ищем все ссылки на новости
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/ru/' in href and '/news/' in href and href.count('/') >= 5:
                        full_url = f"https://news.itmo.ru{href}" if href.startswith('/') else href
                        news_links.append(full_url)
                
                logger.info(f"Найдено {len(news_links[:3])} уникальных новостей")
                return list(dict.fromkeys(news_links[:3]))  # Убираем дубликаты и берем первые 3

    async def _scrape_news_content(self, url: str) -> Dict[str, str]:
        logger.info(f"Получаю содержимое новости: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при чтении новости: {response.status}")
                    return {"title": "", "content": "", "url": url}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                title = ""
                if title_elem := soup.find('h1'):
                    title = title_elem.text.strip()
                
                content = ""
                if article := soup.find('article'):
                    content = article.text.strip()
                
                return {
                    "title": title,
                    "content": content[:1000],  # Ограничиваем размер контента
                    "url": url
                }

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = state["messages"][-1]["content"]
            logger.info(f"Запуск NewsAgent с запросом: {query}")
            
            # Получаем ссылки на новости
            news_links = await self._fetch_news_links(query)
            
            # Собираем контент каждой новости
            scraping_results = []
            logger.info(f"Начинаю сбор контента для {len(news_links)} новостей")
            for link in news_links:
                news_content = await self._scrape_news_content(link)
                if news_content["title"] and news_content["content"]:
                    scraping_results.append(news_content)
            
            logger.info(f"Успешно собран контент для {len(scraping_results)} новостей")
            return {
                **state,
                "scraping_results": scraping_results
            }
        except Exception as e:
            logger.error(f"Ошибка в NewsAgent: {str(e)}", exc_info=True)
            return {
                **state,
                "scraping_results": []
            } 