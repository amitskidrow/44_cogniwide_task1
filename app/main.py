from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.routes import calls  # noqa
from app.logging_config import logger
from app.models.db import init_db

app = FastAPI(title="Voice Agent PoC")

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/call/outbound")
def outbound_call():
    # Placeholder implementation
    return {"message": "Outbound call initiated"}


@app.post("/call/inbound")
def inbound_call():
    # Placeholder implementation
    return {"message": "Inbound call received"}


def create_app() -> FastAPI:
    app = FastAPI(title="Voice Agent API")

    # Register routers
    app.include_router(calls.router)

    # Instrumentation for Prometheus
    Instrumentator().instrument(app).expose(app)

    @app.on_event("startup")
    def _startup() -> None:
        """Initialize application resources."""
        init_db()

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

