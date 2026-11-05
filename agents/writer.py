# agents/writer.py
from agents.base import BaseAgent
from tasks.models import Task


class WriterAgent(BaseAgent):
    name = "writer"
    description = "Redige textos, relatórios, e-mails, resumos, propostas e sínteses. Também é o agente padrão quando nenhum outro se encaixa."
    requires_approval = False
    keywords = ["escreva", "redija", "resuma", "texto", "email", "e-mail", "proposta", "carta", "roteiro", "síntese", "resumo"]

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
            f"Tarefa de redação: {task.title}\n"
            f"Descrição: {task.description}\n"
            f"{contexto_txt}\n\n"
            "Escreva de forma clara, profissional e no tom da AMORIM: amigável, direto, próximo. "
            "Se for síntese de resultados anteriores, integre tudo coerentemente, sem copiar cru. "
            "Se for peça externa (e-mail, proposta), adapte o tom para o destinatário final."
        )

        resultado = _chamar_llm(prompt)
        return {"output": resultado}