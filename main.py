import time
from typing import List
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import HttpUrl
from schemas.request import PredictionRequest, PredictionResponse
from utils.logger import setup_logger
from langchain_openai import ChatOpenAI
from agents.search_agent import SearchAgent
from agents.scraping_agent import ScrapingAgent
from agents.synthesizer_agent import SynthesizerAgent, LLMAnswer
from workflow import create_workflow
from config import settings

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
synthesizer_agent = SynthesizerAgent(llm)

# Создание упрощенного рабочего процесса
workflow = create_workflow(synthesizer_agent)

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
        
        final_state = workflow.invoke(initial_state)
        
        logger.info(f"Final state: {final_state}")
        return PredictionResponse(
            id=body.id,
            answer=final_state["llm_answer"].answer,
            reasoning=final_state["llm_answer"].reasoning,
            sources=[]
        )
        
    except Exception as e:
        logger.error(f"Internal error processing request {body.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
        
    
