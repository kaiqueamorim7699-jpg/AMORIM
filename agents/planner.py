# agents/planner.py
import json
import re
from tasks.models import Plan, Task, TaskState, new_id
from agents.registry import all_agents, get_agent


def criar_plano(objetivo: str) -> Plan:
    """
    Recebe um objetivo do usuário e retorna um Plan.
    - Objetivo simples → Plan com complexity="simple" e 0 tasks
    - Objetivo complexo → Plan com 2-6 tasks encadeadas
    """
    from core.agent import _chamar_llm
    from core.prompts import PLANNER_PROMPT

    # monta lista de agentes disponíveis pro prompt
    agentes_txt = "\n".join(
        f"- {a.name}: {a.description}" for a in all_agents()
    )
    prompt = PLANNER_PROMPT.format(agents=agentes_txt)

    # pede ao LLM pra montar o plano
    raw = _chamar_llm(f"Objetivo do usuário: {objetivo}\n\n{prompt}")
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # fallback: trata como simples (não conseguiu planejar)
        return Plan(
            id=new_id("plan"),
            objective=objetivo,
            complexity="simple",
        )

    complexity = data.get("complexity", "simple")
    tasks_data = data.get("tasks", [])

    # se o LLM disse "simple" mas mandou tasks, confia nas tasks
    if complexity == "simple" and not tasks_data:
        return Plan(
            id=new_id("plan"),
            objective=objetivo,
            complexity="simple",
        )

    plan = Plan(
        id=new_id("plan"),
        objective=objetivo,
        complexity="complex",
    )

    # ─── Cria as Tasks ────────────────────────
    temp_tasks: list[Task] = []
    for i, t in enumerate(tasks_data):
        agent_name = t.get("agent_name", "writer")
        # valida se o agente existe; se não, cai no writer
        if not get_agent(agent_name):
            agent_name = "writer"

        task = Task(
            id=new_id("task"),
            title=t.get("title", f"Tarefa {i+1}"),
            description=t.get("description", ""),
            agent_name=agent_name,
            input_data=t.get("input_data", {}) or {},
        )
        # guarda temporariamente os depends_on (que são índices) num campo auxiliar
        task._temp_depends_idx = t.get("depends_on", []) or []
        temp_tasks.append(task)

    # ─── Resolve depends_on (índice → id real) ─
    for task in temp_tasks:
        indices = getattr(task, "_temp_depends_idx", [])
        task.depends_on = [
            temp_tasks[idx].id
            for idx in indices
            if isinstance(idx, int) and 0 <= idx < len(temp_tasks)
        ]
        delattr(task, "_temp_depends_idx")

    plan.tasks = temp_tasks
    return plan