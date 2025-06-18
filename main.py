from fastapi import FastAPI
from app.api import calls
from app.config import get_settings

settings = get_settings()
app = FastAPI(title="AI Voice Agent")

app.include_router(calls.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
