# agents/registry.py
from agents.base import BaseAgent
from agents.researcher import ResearcherAgent
from agents.business import BusinessAgent
from agents.file_maker import FileMakerAgent
from agents.writer import WriterAgent
from agents.psychology import PsychologyAgent 

_AGENTS: dict[str, BaseAgent] = {}


def _register(agent: BaseAgent) -> None:
    _AGENTS[agent.name] = agent


# Registra todos os agentes disponíveis
_register(ResearcherAgent())
_register(BusinessAgent())
_register(FileMakerAgent())
_register(WriterAgent())
_register(PsychologyAgent()) 


def get_agent(name: str) -> BaseAgent | None:
    return _AGENTS.get(name)


def all_agents() -> list[BaseAgent]:
    return list(_AGENTS.values())


def list_agents() -> list[dict]:
    """Retorna lista formatada pra API/UI."""
    return [
        {
            "name": a.name,
            "description": a.description,
            "requires_approval": a.requires_approval,
        }
        for a in _AGENTS.values()
    ]