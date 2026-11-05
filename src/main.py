# src/main.py
import os
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from core.agent import processar_stream
from core.orchestrator import aprovar_task, rejeitar_task
from core.rag import build_index
from agents.registry import list_agents
from tasks.store import list_plans, load_plan
from tasks import conversations as conv_store

app = FastAPI(title="AMORIM A.I", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("output", exist_ok=True)
os.makedirs("knowledge", exist_ok=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

@app.get("/api/conversations")
async def get_conversations():
    return {"conversations": conv_store.list_conversations()}

@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    c = conv_store.load_conversation(conv_id)
    if not c: return JSONResponse({"error": "não encontrada"}, status_code=404)
    return c

@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    return {"deleted": conv_store.delete_conversation(conv_id)}

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    def event_generator():
        conv_id = req.conversation_id
        if not conv_id:
            conv = conv_store.create_conversation()
            conv_id = conv["id"]
            yield f"data: {json.dumps({'type': 'conversation', 'id': conv_id})}\n\n"

        conv_store.add_message(conv_id, "user", req.message)
        resposta_acumulada = ""
        plan_data = None

        try:
            for tipo, dados in processar_stream(req.message):
                if tipo == "token":
                    resposta_acumulada += dados
                    yield f"data: {json.dumps({'type': 'token', 'content': dados})}\n\n"
                elif tipo == "plan":
                    plan_data = dados
                    yield f"data: {json.dumps({'type': 'plan', 'plan': dados})}\n\n"
                elif tipo == "done":
                    break
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        conv_store.add_message(conv_id, "assistant", resposta_acumulada, plan=plan_data)
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...)):
    filepath = os.path.join("knowledge", file.filename)
    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())
    ok, msg = build_index()
    return {"success": ok, "message": msg}

@app.get("/api/agents")
async def agents():
    return {"agents": list_agents()}

@app.get("/api/health")
async def health():
    return {"status": "ok", "name": "AMORIM A.I"}

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")