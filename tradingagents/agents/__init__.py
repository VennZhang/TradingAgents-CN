import importlib
from typing import Dict, Tuple

from tradingagents.utils.logging_init import get_logger

logger = get_logger("default")

_EXPORTS: Dict[str, Tuple[str, str]] = {
    "FinancialSituationMemory": ("tradingagents.agents.utils.memory", "FinancialSituationMemory"),
    "Toolkit": ("tradingagents.agents.utils.agent_utils", "Toolkit"),
    "create_msg_delete": ("tradingagents.agents.utils.agent_utils", "create_msg_delete"),
    "AgentState": ("tradingagents.agents.utils.agent_states", "AgentState"),
    "InvestDebateState": ("tradingagents.agents.utils.agent_states", "InvestDebateState"),
    "RiskDebateState": ("tradingagents.agents.utils.agent_states", "RiskDebateState"),
    "create_bear_researcher": ("tradingagents.agents.researchers.bear_researcher", "create_bear_researcher"),
    "create_bull_researcher": ("tradingagents.agents.researchers.bull_researcher", "create_bull_researcher"),
    "create_research_manager": ("tradingagents.agents.managers.research_manager", "create_research_manager"),
    "create_fundamentals_analyst": ("tradingagents.agents.analysts.fundamentals_analyst", "create_fundamentals_analyst"),
    "create_market_analyst": ("tradingagents.agents.analysts.market_analyst", "create_market_analyst"),
    "create_news_analyst": ("tradingagents.agents.analysts.news_analyst", "create_news_analyst"),
    "create_social_media_analyst": ("tradingagents.agents.analysts.social_media_analyst", "create_social_media_analyst"),
    "create_risky_debator": ("tradingagents.agents.risk_mgmt.aggresive_debator", "create_risky_debator"),
    "create_safe_debator": ("tradingagents.agents.risk_mgmt.conservative_debator", "create_safe_debator"),
    "create_neutral_debator": ("tradingagents.agents.risk_mgmt.neutral_debator", "create_neutral_debator"),
    "create_risk_manager": ("tradingagents.agents.managers.risk_manager", "create_risk_manager"),
    "create_trader": ("tradingagents.agents.trader.trader", "create_trader"),
    # Index prediction states
    "IndexPredictionState": ("tradingagents.agents.utils.agent_states", "IndexPredictionState"),
    "IndexDebateState": ("tradingagents.agents.utils.agent_states", "IndexDebateState"),
    "IndexRiskDebateState": ("tradingagents.agents.utils.agent_states", "IndexRiskDebateState"),
    # Index prediction analysts
    "create_index_technical_analyst": ("tradingagents.agents.analysts.index_technical_analyst", "create_index_technical_analyst"),
    "create_index_sentiment_analyst": ("tradingagents.agents.analysts.index_sentiment_analyst", "create_index_sentiment_analyst"),
    "create_macro_policy_analyst": ("tradingagents.agents.analysts.macro_policy_analyst", "create_macro_policy_analyst"),
    "create_index_valuation_analyst": ("tradingagents.agents.analysts.index_valuation_analyst", "create_index_valuation_analyst"),
    "create_sector_theme_analyst": ("tradingagents.agents.analysts.sector_theme_analyst", "create_sector_theme_analyst"),
    "create_index_impact_analyst": ("tradingagents.agents.analysts.index_impact_analyst", "create_index_impact_analyst"),
    # Index prediction debate & decision
    "create_index_bull_researcher": ("tradingagents.agents.researchers.index_bull_researcher", "create_index_bull_researcher"),
    "create_index_bear_researcher": ("tradingagents.agents.researchers.index_bear_researcher", "create_index_bear_researcher"),
    "create_index_research_manager": ("tradingagents.agents.managers.index_research_manager", "create_index_research_manager"),
    "create_index_trader": ("tradingagents.agents.trader.index_trader", "create_index_trader"),
    # Index prediction risk management
    "create_index_risky_debater": ("tradingagents.agents.risk_mgmt.index_risky_debater", "create_index_risky_debater"),
    "create_index_safe_debater": ("tradingagents.agents.risk_mgmt.index_safe_debater", "create_index_safe_debater"),
    "create_index_neutral_debater": ("tradingagents.agents.risk_mgmt.index_neutral_debater", "create_index_neutral_debater"),
    "create_index_risk_manager": ("tradingagents.agents.managers.index_risk_manager", "create_index_risk_manager"),
}

__all__ = [
    "FinancialSituationMemory",
    "Toolkit",
    "AgentState",
    "create_msg_delete",
    "InvestDebateState",
    "RiskDebateState",
    "create_bear_researcher",
    "create_bull_researcher",
    "create_research_manager",
    "create_fundamentals_analyst",
    "create_market_analyst",
    "create_neutral_debator",
    "create_news_analyst",
    "create_risky_debator",
    "create_risk_manager",
    "create_safe_debator",
    "create_social_media_analyst",
    "create_trader",
    "IndexPredictionState",
    "IndexDebateState",
    "IndexRiskDebateState",
    "create_index_technical_analyst",
    "create_index_sentiment_analyst",
    "create_macro_policy_analyst",
    "create_index_valuation_analyst",
    "create_sector_theme_analyst",
    "create_index_impact_analyst",
    "create_index_bull_researcher",
    "create_index_bear_researcher",
    "create_index_research_manager",
    "create_index_trader",
    "create_index_risky_debater",
    "create_index_safe_debater",
    "create_index_neutral_debater",
    "create_index_risk_manager",
]


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)

    module_name, attr_name = _EXPORTS[name]
    module = importlib.import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals().keys()) | set(_EXPORTS.keys()))
