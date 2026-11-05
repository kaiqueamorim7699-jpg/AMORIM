# agents/researcher.py
from agents.base import BaseAgent
from tasks.models import Task


class ResearcherAgent(BaseAgent):
    name = "researcher"
    description = "Pesquisa, organiza e analisa informações sobre um tema. Ideal para levantar contexto antes de gerar entregas."
    requires_approval = False
    keywords = ["pesquise", "analise", "compare", "investigue", "estude", "levante"]

    def execute(self, task: Task, context: dict) -> dict:
        from core.agent import _chamar_llm

        # monta contexto das tarefas anteriores (se houver dependências)
        contexto_txt = ""
        if context:
            blocos = []
            for dep_id, res in context.items():
                if isinstance(res, dict) and "output" in res:
                    blocos.append(str(res["output"]))
            if blocos:
                contexto_txt = "\n\nResultados anteriores:\n" + "\n\n".join(blocos)

        prompt = (
            f"Tarefa: {task.title}\n"
            f"Descrição: {task.description}\n"
            f"{contexto_txt}\n\n"
            "Produza uma análise estruturada em tópicos, objetiva e útil para negócios. "
            "Se for relevante, destaque dados, tendências e pontos de atenção. "
            "Não invente números específicos se não tiver dados reais — trabalhe com hipóteses explícitas."
        )

        resultado = _chamar_llm(prompt)
        return {"output": resultado}