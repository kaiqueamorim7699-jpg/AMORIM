# agents/file_maker.py
from agents.base import BaseAgent
from tasks.models import Task
from tools import gerar_excel, gerar_pptx, gerar_pdf, gerar_imagem


class FileMakerAgent(BaseAgent):
    name = "file_maker"
    description = "Gera arquivos: Excel (.xlsx), PowerPoint (.pptx), PDF (.pdf) e imagens (.png)."
    requires_approval = False
    keywords = [
        "excel", "planilha", "xlsx", "powerpoint", "ppt", "pptx", "apresentação", "apresentacao",
        "pdf", "relatório", "relatorio", "imagem", "foto", "desenho", "png"
    ]

    def execute(self, task: Task, context: dict) -> dict:
        from core.agent import _chamar_llm
        import json
        import re

        kind = task.input_data.get("kind", "pdf")

        # ─── EXCEL ────────────────────────────────
        if kind == "excel":
            dados = task.input_data.get("dados")

            # se o Planner não passou dados, pede ao LLM pra estruturar
            if not dados:
                contexto_txt = ""
                if context:
                    contexto_txt = "\n\nContexto:\n" + "\n\n".join(
                        str(r.get("output", "")) for r in context.values() if isinstance(r, dict)
                    )

                raw = _chamar_llm(
                    f"Tarefa: {task.title}\nDescrição: {task.description}{contexto_txt}\n\n"
                    "Retorne APENAS um JSON válido com uma lista de dicionários representando as linhas da planilha. "
                    'Formato: {"dados": [{"coluna1": "valor", "coluna2": "valor"}]}. '
                    "Sem markdown, sem explicação. Use colunas relevantes ao objetivo."
                )
                raw = re.sub(r"```json|```", "", raw).strip()
                try:
                    dados = json.loads(raw).get("dados", [])
                except json.JSONDecodeError:
                    dados = [{"erro": "não foi possível estruturar os dados"}]

            caminho = gerar_excel(dados, titulo_aba=task.input_data.get("titulo_aba", "Dados"))
            return {
                "output": f"Planilha Excel gerada com {len(dados)} linha(s). Caminho: {caminho}",
                "path": caminho,
                "dados_linhas": len(dados),
            }

        # ─── POWERPOINT ───────────────────────────
        if kind == "pptx":
            titulo = task.input_data.get("titulo")
            slides = task.input_data.get("slides")

            if not slides:
                contexto_txt = ""
                if context:
                    contexto_txt = "\n\nContexto:\n" + "\n\n".join(
                        str(r.get("output", "")) for r in context.values() if isinstance(r, dict)
                    )

                raw = _chamar_llm(
                    f"Tarefa: {task.title}\nDescrição: {task.description}{contexto_txt}\n\n"
                    "Crie o conteúdo de uma apresentação profissional. "
                    "Retorne APENAS um JSON válido no formato: "
                    '{"titulo": "...", "slides": [{"titulo": "...", "conteudo": ["bullet1", "bullet2"]}]}. '
                    "De 5 a 10 slides. Sem markdown, sem explicação."
                )
                raw = re.sub(r"```json|```", "", raw).strip()
                try:
                    estrutura = json.loads(raw)
                    titulo = titulo or estrutura.get("titulo", task.title)
                    slides = estrutura.get("slides", [])
                except json.JSONDecodeError:
                    titulo = titulo or task.title
                    slides = [{"titulo": "Erro", "conteudo": ["Não foi possível estruturar a apresentação"]}]

            caminho = gerar_pptx(titulo, slides)
            return {
                "output": f"Apresentação PowerPoint gerada com {len(slides)} slide(s). Caminho: {caminho}",
                "path": caminho,
                "slides": len(slides),
            }

        # ─── IMAGEM ───────────────────────────────
        if kind == "imagem":
            prompt_img = task.input_data.get("prompt") or task.description
            caminho = gerar_imagem(prompt_img)
            return {
                "output": f"Imagem gerada. Caminho: {caminho}",
                "path": caminho,
            }

        # ─── PDF (default) ────────────────────────
        titulo = task.input_data.get("titulo", task.title)
        paragrafos = task.input_data.get("paragrafos")

        if not paragrafos:
            contexto_txt = ""
            if context:
                contexto_txt = "\n\nContexto:\n" + "\n\n".join(
                    str(r.get("output", "")) for r in context.values() if isinstance(r, dict)
                )

            raw = _chamar_llm(
                f"Tarefa: {task.title}\nDescrição: {task.description}{contexto_txt}\n\n"
                "Crie o conteúdo de um relatório profissional. "
                "Retorne APENAS um JSON válido no formato: "
                '{"titulo": "...", "paragrafos": ["par1", "par2", "par3"]}. '
                "De 5 a 12 parágrafos. Sem markdown, sem explicação."
            )
            raw = re.sub(r"```json|```", "", raw).strip()
            try:
                estrutura = json.loads(raw)
                titulo = titulo or estrutura.get("titulo", task.title)
                paragrafos = estrutura.get("paragrafos", [task.description])
            except json.JSONDecodeError:
                paragrafos = [task.description]

        caminho = gerar_pdf(titulo, paragrafos)
        return {
            "output": f"Relatório PDF gerado. Caminho: {caminho}",
            "path": caminho,
            "paragrafos": len(paragrafos),
        }