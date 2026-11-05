# core/agent.py
import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

from core.prompts import SYSTEM_PROMPT
from memory.memory import get_context_string
from tools import gerar_excel, gerar_pptx, gerar_pdf, gerar_imagem
from core.rag import search_knowledge

_client = None
MODEL = os.environ.get("AMORIM_MODEL", "llama-3.1-8b-instant")

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("AMORIM_API_KEY")
        if not api_key or api_key == "gsk_COLE_SUA_CHAVE_AQUI":
            raise RuntimeError("AMORIM_API_KEY não configurada.")
        from groq import Groq
        _client = Groq(api_key=api_key)
    return _client

def _chamar_llm(user_msg: str, contexto_extra: str = "", temperatura: float = 0.7) -> str:
    client = _get_client()
    rag_contexto = search_knowledge(user_msg)

    system = SYSTEM_PROMPT
    if contexto_extra:
        system += f"\n\n## Memória / Contexto\n{contexto_extra}"
    if rag_contexto:
        system += f"\n\n## Base de Conhecimento\n{rag_contexto}"

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
        temperature=temperatura,
        max_tokens=2048,
    )
    return completion.choices[0].message.content

def _detectar_ferramenta(user_msg: str) -> str | None:
    msg = user_msg.lower()
    if any(p in msg for p in ["gere uma imagem", "crie uma imagem", "desenhe", "gere uma foto"]): return "imagem"
    if any(p in msg for p in ["gere um excel", "crie uma planilha", "crie um excel", "gere uma planilha"]): return "excel"
    if any(p in msg for p in ["gere um powerpoint", "crie uma apresentação", "crie um ppt", "gere um ppt"]): return "pptx"
    if any(p in msg for p in ["gere um pdf", "crie um pdf", "gere um relatório pdf"]): return "pdf"
    return None

def _parece_objetivo_complexo(msg: str) -> bool:
    msg_l = msg.lower().strip()
    if len(msg_l) < 40: return False
    gatilhos = ["crie", "faça", "monte", "planeje", "desenvolva", "elabore", "analise e", "e depois", "passo a passo", "relatório completo", "apresentação completa", "plano de", "estratégia para", "e gere", "e crie", "e monte", "com base nisso"]
    return any(g in msg_l for g in gatilhos)

def _executar_ferramenta_direta(ferramenta: str, user_msg: str) -> str:
    if ferramenta == "imagem":
        prompt = user_msg
        for p in ["gere uma imagem", "crie uma imagem", "desenhe", "gere uma foto"]:
            prompt = prompt.lower().replace(p, "")
        caminho = gerar_imagem(prompt.strip(" :,.de ") or "imagem profissional")
        return f"Pronto! Gerei a imagem e salvei em: `{caminho}`"

    if ferramenta == "excel":
        raw = _chamar_llm(f"O usuário pediu: {user_msg}\nRetorne APENAS JSON: {{\"dados\": [{{\"col1\": \"val\"}}]}}")
        raw = re.sub(r"```json|```", "", raw).strip()
        try: dados = json.loads(raw).get("dados", [])
        except: dados = [{"erro": "falha ao estruturar"}]
        return f"Planilha gerada! Salvei em: `{gerar_excel(dados)}`"

    if ferramenta == "pptx":
        raw = _chamar_llm(f"O usuário pediu: {user_msg}\nRetorne APENAS JSON: {{\"titulo\": \"...\", \"slides\": [{{\"titulo\": \"...\", \"conteudo\": [\"b1\"]}}]}}")
        raw = re.sub(r"```json|```", "", raw).strip()
        try:
            est = json.loads(raw)
            return f"Apresentação criada! Salvei em: `{gerar_pptx(est.get('titulo', 'Apresentação'), est.get('slides', []))}`"
        except Exception as e: return f"Erro: {e}"

    if ferramenta == "pdf":
        raw = _chamar_llm(f"O usuário pediu: {user_msg}\nRetorne APENAS JSON: {{\"titulo\": \"...\", \"paragrafos\": [\"p1\"]}}")
        raw = re.sub(r"```json|```", "", raw).strip()
        try:
            est = json.loads(raw)
            return f"Relatório gerado! Salvei em: `{gerar_pdf(est.get('titulo', 'Relatório'), est.get('paragrafos', []))}`"
        except Exception as e: return f"Erro: {e}"
    return "Ferramenta não reconhecida."

def processar(user_msg: str) -> dict:
    if _parece_objetivo_complexo(user_msg):
        try:
            from core.orchestrator import executar_objetivo
            plan = executar_objetivo(user_msg)
            if plan.complexity == "complex" and plan.tasks:
                return {"type": "plan", "plan": plan.to_dict(), "response": plan.final_answer or "Plano executado."}
        except Exception as e: print(f"[orchestrator] erro: {e}")

    ferramenta = _detectar_ferramenta(user_msg)
    if ferramenta:
        try:
            res = _executar_ferramenta_direta(ferramenta, user_msg)
            return {"type": "chat", "response": res}
        except Exception as e:
            return {"type": "chat", "response": f"Erro: {e}"}

    res = _chamar_llm(user_msg, get_context_string())
    return {"type": "chat", "response": res}

def chamar_llm_stream(user_msg: str, contexto_extra: str = "", temperatura: float = 0.7):
    client = _get_client()
    rag_contexto = search_knowledge(user_msg)
    system = SYSTEM_PROMPT
    if contexto_extra: system += f"\n\n## Memória\n{contexto_extra}"
    if rag_contexto: system += f"\n\n## Base de Conhecimento\n{rag_contexto}"

    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
        temperature=temperatura,
        max_tokens=2048,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta: yield delta

def processar_stream(user_msg: str):
    if _parece_objetivo_complexo(user_msg):
        try:
            from core.orchestrator import executar_objetivo
            plan = executar_objetivo(user_msg)
            if plan.complexity == "complex" and plan.tasks:
                yield ("plan", plan.to_dict())
                yield ("token", plan.final_answer or "Plano executado.")
                yield ("done", "")
                return
        except Exception as e: print(f"[stream-orchestrator] erro: {e}")

    ferramenta = _detectar_ferramenta(user_msg)
    if ferramenta:
        try:
            res = _executar_ferramenta_direta(ferramenta, user_msg)
            for i in range(0, len(res), 20): yield ("token", res[i:i+20])
            yield ("done", "")
            return
        except Exception as e:
            yield ("token", f"Erro: {e}")
            yield ("done", "")
            return

    for chunk in chamar_llm_stream(user_msg, get_context_string()):
        yield ("token", chunk)

    yield ("done", "")