import time
import logging

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.conditional_logic import ConditionalLogic
from tradingagents.graph.propagation import Propagator
from tradingagents.graph.index_prediction_setup import IndexPredictionGraphSetup

logger = logging.getLogger(__name__)


class IndexPredictionGraph:
    def __init__(self, debug=False, config=None):
        self.debug = debug
        self.config = config or DEFAULT_CONFIG.copy()

        self.max_debate_rounds = self.config.get("max_debate_rounds", 1)
        self.max_risk_discuss_rounds = self.config.get("max_risk_discuss_rounds", 1)
        self.memory_enabled = self.config.get("memory_enabled", False)
        self.progress_callback = self.config.get("progress_callback", None)

        self.toolkit = Toolkit()

        self.quick_thinking_llm = None
        self.deep_thinking_llm = None
        self._init_llms()

        self.tech_memory = None
        self.sentiment_memory = None
        self.macro_memory = None
        self.valuation_memory = None
        self.sector_memory = None
        self.impact_memory = None
        self.bull_memory = None
        self.bear_memory = None
        self.invest_judge_memory = None
        self.trader_memory = None
        self.risk_manager_memory = None
        if self.memory_enabled:
            self._init_memories()

        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.max_debate_rounds,
            max_risk_discuss_rounds=self.max_risk_discuss_rounds,
        )

        self.graph_setup = None
        self.graph = None
        self._build_graph()

    def _init_llms(self):
        import os
        dashscope_key = self.config.get("DASHSCOPE_API_KEY") or os.environ.get("DASHSCOPE_API_KEY", "")

        quick_model = self.config.get("quick_think_llm", "qwen-plus")
        deep_model = self.config.get("deep_think_llm", "qwen-max")
        quick_cfg = self.config.get("quick_model_config", {})
        deep_cfg = self.config.get("deep_model_config", {})

        from langchain_openai import ChatOpenAI
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        self.quick_thinking_llm = ChatOpenAI(
            model=quick_model,
            temperature=quick_cfg.get("temperature", 0.7),
            max_tokens=quick_cfg.get("max_tokens", 4000),
            api_key=dashscope_key or None,
            base_url=base_url,
            timeout=quick_cfg.get("timeout", 180),
            max_retries=3,
        )
        self.deep_thinking_llm = ChatOpenAI(
            model=deep_model,
            temperature=deep_cfg.get("temperature", 0.3),
            max_tokens=deep_cfg.get("max_tokens", 4000),
            api_key=dashscope_key or None,
            base_url=base_url,
            timeout=deep_cfg.get("timeout", 300),
            max_retries=3,
        )
        logger.info(f"LLM initialized via DashScope OpenAI-compatible: quick={quick_model}, deep={deep_model}, key_len={len(dashscope_key)}")

    def _init_memories(self):
        try:
            mem_kwargs = {"k": 2, "collection_name": "index_predictions"}
            self.bull_memory = FinancialSituationMemory("index_predictions_bull", **mem_kwargs)
            self.bear_memory = FinancialSituationMemory("index_predictions_bear", **mem_kwargs)
            self.invest_judge_memory = FinancialSituationMemory("index_predictions_judge", **mem_kwargs)
            self.trader_memory = FinancialSituationMemory("index_predictions_trader", **mem_kwargs)
            self.risk_manager_memory = FinancialSituationMemory("index_predictions_risk", **mem_kwargs)
            self.tech_memory = FinancialSituationMemory("index_tech_mem", **mem_kwargs)
            self.sentiment_memory = FinancialSituationMemory("index_sent_mem", **mem_kwargs)
            self.macro_memory = FinancialSituationMemory("index_macro_mem", **mem_kwargs)
            self.valuation_memory = FinancialSituationMemory("index_val_mem", **mem_kwargs)
            self.sector_memory = FinancialSituationMemory("index_sector_mem", **mem_kwargs)
            self.impact_memory = FinancialSituationMemory("index_impact_mem", **mem_kwargs)
        except Exception as e:
            logger.warning(f"Failed to init memories: {e}")

    def _build_graph(self):
        memory_config = {
            "tech_memory": self.tech_memory,
            "sentiment_memory": self.sentiment_memory,
            "macro_memory": self.macro_memory,
            "valuation_memory": self.valuation_memory,
            "sector_memory": self.sector_memory,
            "impact_memory": self.impact_memory,
            "bull_memory": self.bull_memory,
            "bear_memory": self.bear_memory,
            "invest_judge_memory": self.invest_judge_memory,
            "trader_memory": self.trader_memory,
            "risk_manager_memory": self.risk_manager_memory,
        }

        self.graph_setup = IndexPredictionGraphSetup(
            quick_thinking_llm=self.quick_thinking_llm,
            deep_thinking_llm=self.deep_thinking_llm,
            toolkit=self.toolkit,
            conditional_logic=self.conditional_logic,
            memory_config=memory_config,
        )
        self.graph = self.graph_setup.setup_graph()

    def propagate(self, user_expectations: str, target_indices: str = None, trade_date: str = None):
        from datetime import datetime

        if target_indices is None:
            target_indices = "000016.SH(上证50), 000300.SH(沪深300), 000905.SH(中证500), 000852.SH(中证1000), 000688.SH(科创50), 399006.SZ(创业板指)"
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        propagator = Propagator(max_recur_limit=200)
        initial_state = propagator.create_initial_index_state(
            user_expectations=user_expectations,
            target_indices=target_indices,
            trade_date=trade_date,
        )

        start_time = time.time()
        final_state = None

        for output in self.graph.stream(initial_state, stream_mode="values", config={"recursion_limit": 200}):
            if self.progress_callback:
                try:
                    if isinstance(output, dict) and any(k in output for k in [
                        "index_technical_report", "index_sentiment_report",
                        "macro_policy_report", "index_valuation_report",
                        "sector_theme_report", "index_impact_report",
                        "index_debate_state", "index_investment_plan",
                        "index_trading_plan", "index_risk_debate_state",
                        "final_index_decision",
                    ]):
                        self.progress_callback(output)
                except Exception as exc:
                    logger.warning(f"Progress callback error: {exc}", exc_info=True)
            final_state = output

        elapsed = time.time() - start_time
        logger.info(f"Index prediction completed in {elapsed:.1f}s")

        if not isinstance(final_state, dict):
            logger.error(f"Invalid final_state type: {type(final_state)}")
            return elapsed, {}

        return elapsed, final_state
