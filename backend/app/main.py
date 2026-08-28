"""FastAPI application entry point for CodePilot V1."""

from fastapi import FastAPI

from app.api.chat import router as chat_router

app = FastAPI(title="CodePilot Agent V1")
app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return service readiness without entering LangGraph or calling a model."""

    return {"status": "ok"}
