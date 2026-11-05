# agents/psychology.py
from agents.base import BaseAgent
from tasks.models import Task


class PsychologyAgent(BaseAgent):
    name = "psychology"
    description = "Especialista em psicologia clínica, psicoeducação, estruturação de sessões, resumos de artigos e ética profissional."
    requires_approval = False
    keywords = [
        "psicologia", "psicólogo", "psicologa", "terapia", "paciente", 
        "ansiedade", "depressão", "depressao", "sessão", "sessao", 
        "clínica", "clinica", "cfp", "anamnese", "psicoeducação",
        "estudo de caso", "tcc", "psicanálise", "psicanalise"
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
            f"Tarefa de Psicologia: {task.title}\n"
            f"Descrição: {task.description}\n"
            f"{contexto_txt}\n\n"
            "Você é um assistente especialista em psicologia. Estruture sua resposta de forma clara, ética e acolhedora. "
            "Se for para criar um material para paciente, use linguagem simples e não-julgadora. "
            "Se for para o profissional, use terminologia técnica adequada (TCC, psicanálise, etc.). "
            "Lembre-se: você não diagnostica, apenas apoia o profissional."
        )

        resultado = _chamar_llm(prompt)
        return {"output": resultado}