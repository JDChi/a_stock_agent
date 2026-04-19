from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import Settings, get_settings
from .llm import create_litellm_model
from .tools import (
    get_company_profile,
    get_financial_indicators,
    get_stock_history,
    get_stock_snapshot,
    search_knowledge,
)

AGENT_NAME = "a_stock_research_agent"

INSTRUCTION = """
You are an A-share research analysis agent.
Use tools for market data and the local knowledge base whenever facts are needed.
Only provide research analysis. Do not provide personalized investment advice,
order placement guidance, position sizing instructions, or trading execution.
Always include source context, data timestamps when available, and uncertainty.
""".strip()


@dataclass
class FallbackAgent:
    name: str
    instruction: str
    tools: list[Any]
    model: Any | None = None


def create_agent(settings: Settings | None = None, model: Any | None = None) -> Any:
    settings = settings or get_settings()
    tools = [
        search_knowledge,
        get_stock_snapshot,
        get_stock_history,
        get_company_profile,
        get_financial_indicators,
    ]
    if model is None:
        try:
            model = create_litellm_model(settings)
        except Exception:
            model = None

    try:
        from google.adk.agents import Agent

        if model is None:
            return FallbackAgent(name=AGENT_NAME, instruction=INSTRUCTION, tools=tools)
        return Agent(
            name=AGENT_NAME,
            model=model,
            instruction=INSTRUCTION,
            tools=tools,
        )
    except Exception:
        return FallbackAgent(name=AGENT_NAME, instruction=INSTRUCTION, tools=tools, model=model)


root_agent = create_agent()
