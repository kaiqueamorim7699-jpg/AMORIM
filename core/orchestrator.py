# core/orchestrator.py
from tasks.models import Plan, Task, TaskState
from tasks.store import save_plan, load_plan
from agents.planner import criar_plano
from agents.registry import get_agent


# ─────────────────────────────────────────────────────────
# PONTO DE ENTRADA
# ─────────────────────────────────────────────────────────
def executar_objetivo(objetivo: str) -> Plan:
    """
    Ponto de entrada do motor.
    Cria o plano e executa até o fim (ou até travar em aprovação).
    Retorna o Plan final.
    """
    plan = criar_plano(objetivo)
    save_plan(plan)

    # objetivo simples: nem executa o loop
    if plan.complexity == "simple" or not plan.tasks:
        plan.status = "done"
        save_plan(plan)
        return plan

    plan.status = "executing"
    save_plan(plan)

    _executar_loop(plan)
    return plan


# ─────────────────────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────
def _executar_loop(plan: Plan) -> None:
    """
    Executa as tasks do plano respeitando dependências, estados e retries.
    Roda até:
      - Todas as tasks chegarem a DONE → status = done
      - Alguma travar em AWAITING_APPROVAL → status = awaiting_approval
      - Alguma FAILED sem retry possível → status = failed
      - Nenhuma task conseguir avançar (deadlock) → break
    """
    max_iteracoes = 50  # proteção contra loop infinito
    iteracoes = 0

    while iteracoes < max_iteracoes:
        iteracoes += 1
        progresso = False

        for task in plan.tasks:
            # só processa tarefas pendentes ou que falharam (pra retry)
            if task.state not in (TaskState.PENDING, TaskState.FAILED):
                continue

            # verifica se todas as dependências estão DONE
            deps_ok = all(
                _get_task(plan, dep_id).state == TaskState.DONE
                for dep_id in task.depends_on
            )
            if not deps_ok:
                continue

            # busca o agente
            agent = get_agent(task.agent_name)
            if not agent:
                task.state = TaskState.FAILED
                task.error = f"Agente '{task.agent_name}' não encontrado"
                _touch(task)
                save_plan(plan)
                progresso = True
                continue

            # precisa de aprovação humana? (só na 1ª tentativa)
            if agent.requires_approval and task.attempts == 0:
                task.state = TaskState.AWAITING_APPROVAL
                _touch(task)
                save_plan(plan)
                progresso = True
                continue

            # ─── EXECUTA ────────────────────────
            task.state = TaskState.RUNNING
            task.attempts += 1
            _touch(task)
            save_plan(plan)

            try:
                # monta contexto com os resultados das dependências
                contexto = {
                    dep_id: _get_task(plan, dep_id).result
                    for dep_id in task.depends_on
                }
                result = agent.execute(task, contexto)

                if not isinstance(result, dict):
                    result = {"output": str(result)}

                task.result = result
                task.state = TaskState.DONE
                task.error = None

            except Exception as e:
                task.error = f"{type(e).__name__}: {e}"
                # reavaliação: se ainda tem tentativas, volta pra PENDING
                if task.attempts < task.max_attempts:
                    task.state = TaskState.PENDING
                else:
                    task.state = TaskState.FAILED

            _touch(task)
            save_plan(plan)
            progresso = True

        # se nada avançou nessa iteração, sai (evita loop infinito)
        if not progresso:
            break

    # ─── Status final do plano ────────────────
    if all(t.state == TaskState.DONE for t in plan.tasks):
        plan.status = "done"
        plan.final_answer = _agregar_resultados(plan)
    elif any(t.state == TaskState.AWAITING_APPROVAL for t in plan.tasks):
        plan.status = "awaiting_approval"
    elif any(t.state == TaskState.FAILED for t in plan.tasks):
        plan.status = "failed"
        plan.final_answer = _sintetizar_falha(plan)
    else:
        plan.status = "failed"

    save_plan(plan)


# ─────────────────────────────────────────────────────────
# AGREGAÇÃO FINAL
# ─────────────────────────────────────────────────────────
def _agregar_resultados(plan: Plan) -> str:
    """Junta os resultados das tasks DONE numa entrega final sintetizada."""
    from core.agent import _chamar_llm
    from core.prompts import AGGREGATOR_PROMPT

    blocos = []
    for t in plan.tasks:
        if t.state == TaskState.DONE and t.result:
            output = t.result.get("output", "") if isinstance(t.result, dict) else str(t.result)
            blocos.append(f"### {t.title}\n{output}")

    if not blocos:
        return "Plano executado sem resultados para sintetizar."

    contexto = "\n\n".join(blocos)

    prompt = (
        f"{AGGREGATOR_PROMPT}\n\n"
        f"---\n"
        f"Objetivo original: {plan.objective}\n\n"
        f"Resultados das tarefas:\n{contexto}\n\n"
        "Agora produza a entrega final pro usuário."
    )

    return _chamar_llm(prompt)


def _sintetizar_falha(plan: Plan) -> str:
    """Quando algo falhou, gera uma explicação amigável e honesta."""
    from core.agent import _chamar_llm

    falhas = [
        f"- {t.title} (agente: {t.agent_name}): {t.error}"
        for t in plan.tasks if t.state == TaskState.FAILED
    ]
    sucessos = [
        f"- {t.title}: {t.result.get('output', '')[:200]}..."
        for t in plan.tasks if t.state == TaskState.DONE and t.result
    ]

    prompt = (
        f"Objetivo: {plan.objective}\n\n"
        f"Tarefas que falharam:\n{chr(10).join(falhas)}\n\n"
        f"Tarefas que deram certo:\n{chr(10).join(sucessos) if sucessos else 'nenhuma'}\n\n"
        "Explique ao usuário, de forma gentil e honesta, o que deu errado, "
        "o que deu certo, e o que ele pode fazer pra tentar de novo ou contornar. "
        "Sem desculpas vazias, sem techniquês. Tom de parceiro."
    )
    return _chamar_llm(prompt)


# ─────────────────────────────────────────────────────────
# APROVAÇÃO HUMANA
# ─────────────────────────────────────────────────────────
def aprovar_task(plan_id: str, task_id: str) -> Plan | None:
    """Aprova uma task em awaiting_approval e continua a execução."""
    plan = load_plan(plan_id)
    if not plan:
        return None

    task = _get_task(plan, task_id)
    if task.state != TaskState.AWAITING_APPROVAL:
        return plan  # nada a fazer

    # volta pra PENDING pra ser executada agora
    task.state = TaskState.PENDING
    _touch(task)
    save_plan(plan)

    # retoma o motor
    _executar_loop(plan)
    return plan


def rejeitar_task(plan_id: str, task_id: str) -> Plan | None:
    """Rejeita uma task em awaiting_approval. Ela vira FAILED."""
    plan = load_plan(plan_id)
    if not plan:
        return None

    task = _get_task(plan, task_id)
    if task.state != TaskState.AWAITING_APPROVAL:
        return plan

    task.state = TaskState.FAILED
    task.error = "Rejeitada pelo usuário"
    _touch(task)

    # atualiza status do plano
    if any(t.state == TaskState.AWAITING_APPROVAL for t in plan.tasks):
        plan.status = "awaiting_approval"
    elif all(t.state == TaskState.DONE for t in plan.tasks):
        plan.status = "done"
        plan.final_answer = _agregar_resultados(plan)
    else:
        plan.status = "failed"

    save_plan(plan)
    return plan


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def _get_task(plan: Plan, task_id: str) -> Task:
    for t in plan.tasks:
        if t.id == task_id:
            return t
    raise KeyError(f"task {task_id} não encontrada no plano {plan.id}")


def _touch(task: Task) -> None:
    """Atualiza o updated_at da task."""
    from datetime import datetime
    task.updated_at = datetime.now().isoformat()