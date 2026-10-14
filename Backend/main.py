import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Ensure Backend directory is in sys.path so ollama_service is found regardless of cwd
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from ollama_service import ollama_service

app = FastAPI(
    title="Customer Support Chatbot API",
    description="FastAPI service for local Ollama customer support models",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Request/Response Models ----------
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None


class GenerateRequest(BaseModel):
    prompt: str
    system: Optional[str] = None


class ChatResponse(BaseModel):
    response: str


# Model for compatibility with frontend home.html (/api/chat)
class SimpleMessageRequest(BaseModel):
    message: str


class SimpleMessageResponse(BaseModel):
    reply: str


# ---------- Health and Info Routes ----------
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "FastAPI Ollama Chatbot API",
        "endpoints": {
            "health": "/health",
            "frontend_chat": "POST /api/chat",
            "generate": "POST /api/ai/generate",
            "chat": "POST /api/ai/chat",
            "stream": "POST /api/ai/stream",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    ollama_ok = ollama_service.is_available()
    return {
        "status": "healthy" if ollama_ok else "degraded",
        "ollama_connected": ollama_ok,
        "ollama_host": ollama_service.host,
        "model": ollama_service.model
    }


# ---------- Compatible route for frontend (/api/chat) ----------
@app.post("/api/chat", response_model=SimpleMessageResponse)
async def api_chat_compat(req: SimpleMessageRequest):
    """Compatible with the frontend UI in Forntend/home.html."""
    try:
        reply = ollama_service.generate(req.message)
        return SimpleMessageResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Ollama AI Routes ----------
@app.post("/api/ai/generate", response_model=ChatResponse)
async def generate(req: GenerateRequest):
    try:
        result = ollama_service.generate(req.prompt, req.system)
        return ChatResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        # Pydantic v2 model_dump with fallback to v1 dict
        messages = [
            m.model_dump() if hasattr(m, "model_dump") else m.dict()
            for m in req.messages
        ]
        result = ollama_service.chat(messages)
        return ChatResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/stream")
async def stream(req: GenerateRequest):
    def event_stream():
        for chunk in ollama_service.stream_generate(req.prompt):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI Ollama server on http://127.0.0.1:8000 ...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)