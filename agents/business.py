# agents/business.py
from agents.base import BaseAgent
from tasks.models import Task


class BusinessAgent(BaseAgent):
    name = "business"
    description = "Especialista em negócios: financeiro, marketing, estratégia, KPIs, análise de mercado e recomendações práticas."
    requires_approval = False
    keywords = [
        "negócio", "negocios", "financeiro", "receita", "custo", "lucro", "margem",
        "kpi", "estratégia", "estrategia", "marketing", "vendas", "funil",
        "cac", "ltv", "precificação", "mercado", "concorrência", "swot", "okr"
    ]

    def execute(self, task: Task, context: dict) -> dict:
        from core.agent import _chamar_llm

        contexto_txt = ""
        if context:
            blocos = []
            for res in context.values():
                if isinstance(res, dict) and "output" in res:
                    blocos.append(str(res["output"]))
            if blocos:
                contexto_txt = "\n\nResultados anteriores:\n" + "\n\n".join(blocos)

        prompt = (
            f"Tarefa de negócios: {task.title}\n"
            f"Descrição: {task.description}\n"
            f"{contexto_txt}\n\n"
            "Você é um consultor sênior de negócios. Traga uma análise prática com:\n"
            "- Diagnóstico direto do cenário\n"
            "- Riscos e oportunidades\n"
            "- Recomendações concretas (o que fazer, em que ordem)\n"
            "- Métricas para acompanhar\n\n"
            "Use números quando possível, mas não invente dados que você não tem. "
            "Se faltar informação, faça hipóteses explícitas. Seja direto e acionável."
        )

        resultado = _chamar_llm(prompt)
        return {"output": resultado}