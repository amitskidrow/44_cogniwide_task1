from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.routes import calls  # noqa
from app.logging_config import logger


def create_app() -> FastAPI:
    app = FastAPI(title="Voice Agent API")

    # Register routers
    app.include_router(calls.router)

    # Instrumentation for Prometheus
    Instrumentator().instrument(app).expose(app)

    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.bind(path=request.url.path, method=request.method).info("request_start")
        response = await call_next(request)
        logger.bind(path=request.url.path, method=request.method, status=response.status_code).info(
            "request_end"
        )
        return response

    return app


app = create_app()
