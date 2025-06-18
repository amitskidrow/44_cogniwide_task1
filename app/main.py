from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.routes.calls import router as calls_router
from app.routes.config import router as config_router
from app.logging_config import logger
from app.models.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="Voice Agent API")

    app.add_event_handler("startup", init_db)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    app.include_router(calls_router)
    app.include_router(config_router)

    Instrumentator().instrument(app).expose(app)

    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.bind(path=request.url.path, method=request.method).info("request_start")
        response = await call_next(request)
        logger.bind(path=request.url.path, method=request.method, status=response.status_code).info("request_end")
        return response

    return app


app = create_app()

