# memory/memory.py
import json
import os
from datetime import datetime

MEMORY_FILE = "memory/amorim_memory.json"


def _ensure_file() -> None:
    """Garante que a pasta e o arquivo existem."""
    os.makedirs("memory", exist_ok=True)
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"facts": [], "conversations": []}, f, ensure_ascii=False, indent=2)


def load_memory() -> dict:
    """Carrega a memória do disco."""
    _ensure_file()
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory: dict) -> None:
    """Salva a memória no disco."""
    _ensure_file()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_fact(fact: str) -> None:
    """Salva um fato duradouro sobre o usuário (ex: 'trabalha com vendas')."""
    mem = load_memory()
    mem["facts"].append({
        "text": fact,
        "date": datetime.now().isoformat(),
    })
    # mantém só os 50 fatos mais recentes
    mem["facts"] = mem["facts"][-50:]
    save_memory(mem)


def add_conversation(user_msg: str, assistant_msg: str) -> None:
    """Salva o turno da conversa (últimas 20)."""
    mem = load_memory()
    mem["conversations"].append({
        "user": user_msg,
        "assistant": assistant_msg,
        "date": datetime.now().isoformat(),
    })
    # mantém só as últimas 20 conversas
    mem["conversations"] = mem["conversations"][-20:]
    save_memory(mem)


def get_context_string() -> str:
    """
    Monta o contexto de memória pra injetar no prompt do LLM.
    Inclui fatos duradouros + últimas conversas.
    """
    mem = load_memory()
    parts = []

    if mem.get("facts"):
        parts.append("Fatos que você lembra sobre o usuário:")
        for f in mem["facts"][-10:]:
            parts.append(f"- {f['text']}")

    if mem.get("conversations"):
        parts.append("\nÚltimas conversas:")
        for c in mem["conversations"][-5:]:
            user_trunc = c["user"][:200]
            asst_trunc = c["assistant"][:200]
            parts.append(f"Usuário: {user_trunc}")
            parts.append(f"AMORIM: {asst_trunc}")

    return "\n".join(parts) if parts else ""


def clear_memory() -> None:
    """Limpa toda a memória (útil pra testes)."""
    save_memory({"facts": [], "conversations": []})