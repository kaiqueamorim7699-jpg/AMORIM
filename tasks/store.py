# tasks/store.py
import json
import os
from tasks.models import Plan

PLANS_DIR = "tasks/plans"
os.makedirs(PLANS_DIR, exist_ok=True)


def _path(plan_id: str) -> str:
    return os.path.join(PLANS_DIR, f"{plan_id}.json")


def save_plan(plan: Plan) -> None:
    """Salva o plano em disco (sobrescreve se já existir)."""
    with open(_path(plan.id), "w", encoding="utf-8") as f:
        json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)


def load_plan(plan_id: str) -> Plan | None:
    """Carrega um plano salvo. Retorna None se não existir."""
    p = _path(plan_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return Plan.from_dict(json.load(f))


def list_plans() -> list[str]:
    """Lista os ids de todos os planos salvos."""
    if not os.path.exists(PLANS_DIR):
        return []
    return [
        f.replace(".json", "")
        for f in os.listdir(PLANS_DIR)
        if f.endswith(".json")
    ]


def delete_plan(plan_id: str) -> bool:
    """Remove um plano do disco."""
    p = _path(plan_id)
    if os.path.exists(p):
        os.remove(p)
        return True
    return False