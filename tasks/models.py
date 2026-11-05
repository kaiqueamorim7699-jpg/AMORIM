# tasks/models.py
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid


# ─────────────────────────────────────────────────────────
# ESTADOS DA TAREFA (exatamente os 5 que você pediu)
# ─────────────────────────────────────────────────────────
class TaskState(str, Enum):
    PENDING = "pending"                       # ⏳ aguardando vez
    RUNNING = "running"                       # 🔄 em execução
    AWAITING_APPROVAL = "awaiting_approval"   # ✋ aguardando aprovação humana
    DONE = "done"                             # ✅ concluída
    FAILED = "failed"                         # ❌ falhou


# ─────────────────────────────────────────────────────────
# TASK (uma tarefa atômica do plano)
# ─────────────────────────────────────────────────────────
@dataclass
class Task:
    id: str
    title: str
    description: str
    agent_name: str                                   # qual agente executa
    input_data: dict = field(default_factory=dict)    # dados de entrada
    depends_on: list[str] = field(default_factory=list)  # ids de tasks anteriores
    state: TaskState = TaskState.PENDING
    result: dict | None = None                        # saída do agente
    error: str | None = None                          # mensagem se falhou
    attempts: int = 0                                 # tentativas já feitas
    max_attempts: int = 2                             # limite de retries
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state"] = self.state.value
        return d

    @staticmethod
    def from_dict(d: dict) -> "Task":
        d = dict(d)
        d["state"] = TaskState(d["state"])
        return Task(**d)


# ─────────────────────────────────────────────────────────
# PLAN (o plano completo do objetivo)
# ─────────────────────────────────────────────────────────
@dataclass
class Plan:
    id: str
    objective: str                                   # objetivo original do usuário
    complexity: str                                  # "simple" | "complex"
    tasks: list[Task] = field(default_factory=list)
    status: str = "planning"                         # planning | executing | awaiting_approval | done | failed
    final_answer: str | None = None                  # entrega final sintetizada
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "objective": self.objective,
            "complexity": self.complexity,
            "tasks": [t.to_dict() for t in self.tasks],
            "status": self.status,
            "final_answer": self.final_answer,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Plan":
        return Plan(
            id=d["id"],
            objective=d["objective"],
            complexity=d["complexity"],
            tasks=[Task.from_dict(t) for t in d["tasks"]],
            status=d["status"],
            final_answer=d.get("final_answer"),
            created_at=d["created_at"],
        )


# ─────────────────────────────────────────────────────────
# Utilidade: gera id único
# ─────────────────────────────────────────────────────────
def new_id(prefixo: str = "task") -> str:
    return f"{prefixo}_{uuid.uuid4().hex[:8]}"