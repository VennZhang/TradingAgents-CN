from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from tradingagents.agents.utils.agent_states import IndexPredictionState, IndexDebateState, IndexRiskDebateState
from tradingagents.graph.conditional_logic import ConditionalLogic


def _create_index_msg_clear():
    from langchain_core.messages import HumanMessage, RemoveMessage

    def clear_node(state):
        messages = state.get("messages", [])
        ops = []
        for m in messages:
            if hasattr(m, 'id') and m.id:
                ops.append(RemoveMessage(id=m.id))
        ops.append(HumanMessage(content="continue"))
        return {"messages": ops}

    return clear_node


class IndexPredictionGraphSetup:
    def __init__(self, quick_thinking_llm, deep_thinking_llm, toolkit, conditional_logic, memory_config):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.toolkit = toolkit
        self.conditional_logic = conditional_logic
        self.memory_config = memory_config

        self.tech_memory = memory_config.get("tech_memory")
        self.sentiment_memory = memory_config.get("sentiment_memory")
        self.macro_memory = memory_config.get("macro_memory")
        self.valuation_memory = memory_config.get("valuation_memory")
        self.sector_memory = memory_config.get("sector_memory")
        self.impact_memory = memory_config.get("impact_memory")
        self.bull_memory = memory_config.get("bull_memory")
        self.bear_memory = memory_config.get("bear_memory")
        self.invest_judge_memory = memory_config.get("invest_judge_memory")
        self.trader_memory = memory_config.get("trader_memory")
        self.risk_manager_memory = memory_config.get("risk_manager_memory")

        self.tool_nodes = {
            "tech": ToolNode([
                self.toolkit.get_index_data,
            ]),
            "sentiment": ToolNode([
                self.toolkit.get_futures_sentiment_data,
                self.toolkit.get_fund_flow_data,
                self.toolkit.get_margin_data,
            ]),
            "macro": ToolNode([
                self.toolkit.get_macro_news,
                self.toolkit.get_index_data,
            ]),
            "valuation": ToolNode([
                self.toolkit.get_index_valuation_data,
                self.toolkit.get_index_constituents,
                self.toolkit.get_index_sector_weights,
            ]),
            "sector": ToolNode([
                self.toolkit.get_sector_performance,
                self.toolkit.get_sector_list,
            ]),
            "impact": ToolNode([
                self.toolkit.get_index_constituents,
                self.toolkit.get_index_sector_weights,
            ]),
        }

    def setup_graph(self):
        from tradingagents.agents import (
            create_index_technical_analyst,
            create_index_sentiment_analyst,
            create_macro_policy_analyst,
            create_index_valuation_analyst,
            create_sector_theme_analyst,
            create_index_impact_analyst,
            create_index_bull_researcher,
            create_index_bear_researcher,
            create_index_research_manager,
            create_index_trader,
            create_index_risky_debater,
            create_index_safe_debater,
            create_index_neutral_debater,
            create_index_risk_manager,
        )

        workflow = StateGraph(IndexPredictionState)

        analyst_nodes = {
            "tech": create_index_technical_analyst(self.quick_thinking_llm, self.toolkit),
            "sentiment": create_index_sentiment_analyst(self.quick_thinking_llm, self.toolkit),
            "macro": create_macro_policy_analyst(self.quick_thinking_llm, self.toolkit),
            "valuation": create_index_valuation_analyst(self.quick_thinking_llm, self.toolkit),
            "sector": create_sector_theme_analyst(self.quick_thinking_llm, self.toolkit),
            "impact": create_index_impact_analyst(self.quick_thinking_llm, self.toolkit),
        }

        delete_nodes = {k: _create_index_msg_clear() for k in analyst_nodes}

        bull_node = create_index_bull_researcher(self.quick_thinking_llm, self.bull_memory)
        bear_node = create_index_bear_researcher(self.quick_thinking_llm, self.bear_memory)
        research_manager_node = create_index_research_manager(self.deep_thinking_llm, self.invest_judge_memory)
        trader_node = create_index_trader(self.quick_thinking_llm, self.trader_memory)
        risky_node = create_index_risky_debater(self.quick_thinking_llm)
        safe_node = create_index_safe_debater(self.quick_thinking_llm)
        neutral_node = create_index_neutral_debater(self.quick_thinking_llm)
        risk_manager_node = create_index_risk_manager(self.deep_thinking_llm, self.risk_manager_memory)

        workflow.add_node("Index Technical Analyst", analyst_nodes["tech"])
        workflow.add_node("tool_tech", self.tool_nodes["tech"])
        workflow.add_node("msg_clear_tech", delete_nodes["tech"])

        workflow.add_node("Index Sentiment Analyst", analyst_nodes["sentiment"])
        workflow.add_node("tool_sentiment", self.tool_nodes["sentiment"])
        workflow.add_node("msg_clear_sentiment", delete_nodes["sentiment"])

        workflow.add_node("Macro Policy Analyst", analyst_nodes["macro"])
        workflow.add_node("tool_macro", self.tool_nodes["macro"])
        workflow.add_node("msg_clear_macro", delete_nodes["macro"])

        workflow.add_node("Index Valuation Analyst", analyst_nodes["valuation"])
        workflow.add_node("tool_valuation", self.tool_nodes["valuation"])
        workflow.add_node("msg_clear_valuation", delete_nodes["valuation"])

        workflow.add_node("Sector Theme Analyst", analyst_nodes["sector"])
        workflow.add_node("tool_sector", self.tool_nodes["sector"])
        workflow.add_node("msg_clear_sector", delete_nodes["sector"])

        workflow.add_node("Index Impact Analyst", analyst_nodes["impact"])
        workflow.add_node("tool_impact", self.tool_nodes["impact"])
        workflow.add_node("msg_clear_impact", delete_nodes["impact"])

        workflow.add_node("Index Bull Researcher", bull_node)
        workflow.add_node("Index Bear Researcher", bear_node)
        workflow.add_node("Index Research Manager", research_manager_node)
        workflow.add_node("Index Trader", trader_node)

        workflow.add_node("Index Risky Debater", risky_node)
        workflow.add_node("Index Safe Debater", safe_node)
        workflow.add_node("Index Neutral Debater", neutral_node)
        workflow.add_node("Index Risk Manager", risk_manager_node)

        workflow.add_edge(START, "Index Technical Analyst")

        workflow.add_conditional_edges("Index Technical Analyst", self.conditional_logic.should_continue_tech, {
            "tool_tech": "tool_tech",
            "msg_clear_tech": "msg_clear_tech",
        })
        workflow.add_edge("tool_tech", "Index Technical Analyst")
        workflow.add_edge("msg_clear_tech", "Index Sentiment Analyst")

        workflow.add_conditional_edges("Index Sentiment Analyst", self.conditional_logic.should_continue_sentiment, {
            "tool_sentiment": "tool_sentiment",
            "msg_clear_sentiment": "msg_clear_sentiment",
        })
        workflow.add_edge("tool_sentiment", "Index Sentiment Analyst")
        workflow.add_edge("msg_clear_sentiment", "Macro Policy Analyst")

        workflow.add_conditional_edges("Macro Policy Analyst", self.conditional_logic.should_continue_macro_policy, {
            "tool_macro": "tool_macro",
            "msg_clear_macro": "msg_clear_macro",
        })
        workflow.add_edge("tool_macro", "Macro Policy Analyst")
        workflow.add_edge("msg_clear_macro", "Index Valuation Analyst")

        workflow.add_conditional_edges("Index Valuation Analyst", self.conditional_logic.should_continue_valuation, {
            "tool_valuation": "tool_valuation",
            "msg_clear_valuation": "msg_clear_valuation",
        })
        workflow.add_edge("tool_valuation", "Index Valuation Analyst")
        workflow.add_edge("msg_clear_valuation", "Sector Theme Analyst")

        workflow.add_conditional_edges("Sector Theme Analyst", self.conditional_logic.should_continue_sector, {
            "msg_clear_sector": "msg_clear_sector",
            "tool_sector": "tool_sector",
        })
        workflow.add_edge("tool_sector", "Sector Theme Analyst")
        workflow.add_edge("msg_clear_sector", "Index Impact Analyst")

        workflow.add_conditional_edges("Index Impact Analyst", self.conditional_logic.should_continue_index_impact, {
            "msg_clear_impact": "msg_clear_impact",
            "tool_impact": "tool_impact",
        })
        workflow.add_edge("tool_impact", "Index Impact Analyst")
        workflow.add_edge("msg_clear_impact", "Index Bull Researcher")

        workflow.add_edge("Index Bull Researcher", "Index Bear Researcher")
        workflow.add_conditional_edges("Index Bear Researcher", self.conditional_logic.should_continue_index_debate, {
            "Index Bull Researcher": "Index Bull Researcher",
            "Index Research Manager": "Index Research Manager",
        })

        workflow.add_edge("Index Research Manager", "Index Trader")

        workflow.add_edge("Index Trader", "Index Risky Debater")
        workflow.add_edge("Index Risky Debater", "Index Safe Debater")
        workflow.add_edge("Index Safe Debater", "Index Neutral Debater")
        workflow.add_conditional_edges("Index Neutral Debater", self.conditional_logic.should_continue_index_risk, {
            "Index Risky Debater": "Index Risky Debater",
            "Index Risk Manager": "Index Risk Manager",
        })

        workflow.add_edge("Index Risk Manager", END)

        return workflow.compile()
