# TradingAgents/graph/propagation.py

from typing import Dict, Any

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
    IndexDebateState,
    IndexRiskDebateState,
    IndexPredictionState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, company_name: str, trade_date: str
    ) -> Dict[str, Any]:
        """Create the initial state for the agent graph."""
        from langchain_core.messages import HumanMessage

        # 🔥 修复：创建明确的分析请求消息，而不是只传递股票代码
        # 这样可以确保所有LLM（包括DeepSeek）都能理解任务
        analysis_request = f"请对股票 {company_name} 进行全面分析，交易日期为 {trade_date}。"

        return {
            "messages": [HumanMessage(content=analysis_request)],
            "company_of_interest": company_name,
            "trade_date": str(trade_date),
            "investment_debate_state": InvestDebateState(
                {"history": "", "current_response": "", "count": 0}
            ),
            "risk_debate_state": RiskDebateState(
                {
                    "history": "",
                    "current_risky_response": "",
                    "current_safe_response": "",
                    "current_neutral_response": "",
                    "count": 0,
                }
            ),
            "market_report": "",
            "fundamentals_report": "",
            "sentiment_report": "",
            "news_report": "",
        }

    def get_graph_args(self, use_progress_callback: bool = False) -> Dict[str, Any]:
        stream_mode = "updates" if use_progress_callback else "values"
        return {
            "stream_mode": stream_mode,
            "config": {"recursion_limit": self.max_recur_limit},
        }

    def create_initial_index_state(
        self, user_expectations: str, target_indices: str, trade_date: str
    ) -> Dict[str, Any]:
        from langchain_core.messages import HumanMessage

        analysis_request = f"请对以下指数进行预测分析，目标指数: {target_indices}"

        return {
            "messages": [HumanMessage(content=analysis_request)],
            "user_expectations": user_expectations or "",
            "target_indices": target_indices,
            "trade_date": str(trade_date),
            "sender": "",
            "index_technical_report": "",
            "index_sentiment_report": "",
            "macro_policy_report": "",
            "index_valuation_report": "",
            "sector_theme_report": "",
            "index_impact_report": "",
            "index_debate_state": IndexDebateState({"history": "", "current_response": "", "count": 0}),
            "index_investment_plan": "",
            "index_trading_plan": "",
            "index_risk_debate_state": IndexRiskDebateState({
                "risky_history": "", "safe_history": "", "neutral_history": "",
                "history": "", "latest_speaker": "",
                "current_risky_response": "", "current_safe_response": "",
                "current_neutral_response": "", "judge_decision": "", "count": 0,
            }),
            "final_index_decision": "",
            "tech_tool_call_count": 0,
            "sentiment_tool_call_count": 0,
            "macro_tool_call_count": 0,
            "valuation_tool_call_count": 0,
            "sector_tool_call_count": 0,
            "impact_tool_call_count": 0,
        }
