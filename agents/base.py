# agents/base.py
from abc import ABC, abstractmethod
from tasks.models import Task


class BaseAgent(ABC):
    """
    Contrato base de todo agente da AMORIM A.I.
    Pra criar um agente novo, basta herdar dessa classe e implementar execute().
    """

    name: str = "base"
    description: str = "Agente genérico"
    requires_approval: bool = False     # se True, task vai pra awaiting_approval antes de rodar
    keywords: list[str] = []            # palavras que indicam que esse agente deve ser escolhido

    @abstractmethod
    def execute(self, task: Task, context: dict) -> dict:
        """
        Executa a tarefa.

        Args:
            task: a Task a ser executada
            context: dict {task_id: result} com os resultados das tarefas das quais essa depende

        Returns:
            dict com pelo menos {"output": <str ou dado>}. Pode incluir "path" se gerou arquivo.

        Raises:
            Qualquer exceção = task marcada como FAILED (ou retentada se ainda tiver attempts).
        """
        ...

    def can_handle(self, objective: str) -> bool:
        """Heurística simples: verifica se a descrição contém alguma keyword."""
        obj = objective.lower()
        return any(k in obj for k in self.keywords)

    def __repr__(self):
        return f"<Agent {self.name}>"