import time
from typing import List
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import HttpUrl
from schemas.request import PredictionRequest, PredictionResponse
from utils.logger import setup_logger
from langchain_openai import ChatOpenAI
from agents.search_agent import SearchAgent
from agents.news_agent import NewsAgent
from agents.synthesizer_agent import SynthesizerAgent, LLMAnswer
from workflow import create_workflow
from config import settings
from agents.query_extractor_agent import QueryExtractorAgent

app = FastAPI()
logger = None

@app.on_event("startup")
async def startup_event():
    global logger
    logger = setup_logger()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    body = await request.body()
    logger.info(
        f"Incoming request: {request.method} {request.url}\n"
        f"Request body: {body.decode()}"
    )

    response = await call_next(request)
    process_time = time.time() - start_time

    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    logger.info(
        f"Request completed: {request.method} {request.url}\n"
        f"Status: {response.status_code}\n"
        f"Response body: {response_body.decode()}\n"
        f"Duration: {process_time:.3f}s"
    )

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )
    
llm = ChatOpenAI(
    api_key=settings.OPENAI_API_KEY,
    temperature=settings.OPENAI_TEMPERATURE,
    model=settings.OPENAI_MODEL_NAME
)

query_extractor_llm = ChatOpenAI(
    api_key=settings.OPENAI_API_KEY,
    temperature=settings.OPENAI_TEMPERATURE,
    model=settings.QUERY_EXTRACTOR_MODEL_NAME
)

search_agent = SearchAgent(llm)
synthesizer_agent = SynthesizerAgent(llm)
news_agent = NewsAgent(llm)
query_extractor_agent = QueryExtractorAgent(query_extractor_llm)

workflow = create_workflow(
    synthesizer_agent=synthesizer_agent,
    search_agent=search_agent,
    news_agent=news_agent,
    query_extractor_agent=query_extractor_agent
)

@app.post("/api/request", response_model=PredictionResponse)
async def predict(body: PredictionRequest):
    try:
        initial_state = {
            "messages": [{"role": "user", "content": body.query}],
            "current_step": "start",
            "scraping_results": [],
            "search_results": [],
            "llm_answer": LLMAnswer(
                answer=0,
                reasoning=""
            )
        }
        
        final_state = await workflow.ainvoke(initial_state)
        
        logger.info(f"Final state: {final_state}")
        return PredictionResponse(
            id=body.id,
            answer=final_state["llm_answer"].answer,
            reasoning=f"{final_state['llm_answer'].reasoning}\n\n Ответ сгенерирован моделью gpt-4-turbo-preview",
            sources=[
                result["url"]
                for result in final_state["search_results"]
            ][:3]
        )
        
    except Exception as e:
        logger.error(f"Internal error processing request {body.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
