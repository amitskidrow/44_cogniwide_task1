from fastapi import FastAPI

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
