# tasks/conversations.py
import json
import os
from datetime import datetime
import uuid

CONV_DIR = "tasks/conversations"
os.makedirs(CONV_DIR, exist_ok=True)


def _path(conv_id: str) -> str:
    return os.path.join(CONV_DIR, f"{conv_id}.json")


def new_conversation_id() -> str:
    return f"conv_{uuid.uuid4().hex[:8]}"


def create_conversation(title: str = "Nova conversa") -> dict:
    conv_id = new_conversation_id()
    conv = {
        "id": conv_id,
        "title": title,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "messages": [],
    }
    _save(conv)
    return conv


def _save(conv: dict) -> None:
    conv["updated_at"] = datetime.now().isoformat()
    with open(_path(conv["id"]), "w", encoding="utf-8") as f:
        json.dump(conv, f, ensure_ascii=False, indent=2)


def load_conversation(conv_id: str) -> dict | None:
    p = _path(conv_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def list_conversations() -> list[dict]:
    """Retorna lista de conversas (só metadados) ordenada por updated_at desc."""
    if not os.path.exists(CONV_DIR):
        return []
    convs = []
    for fname in os.listdir(CONV_DIR):
        if not fname.endswith(".json"):
            continue
        p = os.path.join(CONV_DIR, fname)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            convs.append({
                "id": data["id"],
                "title": data["title"],
                "updated_at": data["updated_at"],
                "message_count": len(data.get("messages", [])),
            })
    convs.sort(key=lambda c: c["updated_at"], reverse=True)
    return convs


def add_message(conv_id: str, role: str, content: str, plan: dict | None = None) -> dict | None:
    """Adiciona mensagem à conversa. role = 'user' | 'assistant'."""
    conv = load_conversation(conv_id)
    if not conv:
        return None
    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }
    if plan:
        msg["plan"] = plan
    conv["messages"].append(msg)

    # Se for a primeira mensagem do usuário e o título for genérico, atualiza
    if role == "user" and conv["title"] == "Nova conversa":
        conv["title"] = content[:50] + ("..." if len(content) > 50 else "")

    _save(conv)
    return conv


def delete_conversation(conv_id: str) -> bool:
    p = _path(conv_id)
    if os.path.exists(p):
        os.remove(p)
        return True
    return False