import asyncio
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional

from app.utils.timezone import now_tz
from tradingagents.utils.logging_init import get_logger

logger = get_logger("default")

DEPTH_MAP = {
    "快速": {"debate_rounds": 1, "risk_rounds": 1, "memory_enabled": False},
    "基础": {"debate_rounds": 1, "risk_rounds": 1, "memory_enabled": True},
    "标准": {"debate_rounds": 1, "risk_rounds": 2, "memory_enabled": True},
    "深度": {"debate_rounds": 2, "risk_rounds": 2, "memory_enabled": True},
    "全面": {"debate_rounds": 3, "risk_rounds": 3, "memory_enabled": True},
}

STEP_MAP = {
    "index_technical": ("指数技术面分析师", "分析六大指数的K线趋势、技术指标和量价关系"),
    "index_sentiment": ("资金情绪分析师", "分析期货持仓、北向资金和融资融券情绪"),
    "macro_policy": ("宏观政策分析师", "解读宏观经济数据、政策取向和全球事件"),
    "index_valuation": ("指数估值分析师", "评估各指数PE/PB历史分位和板块结构"),
    "sector_theme": ("板块主线分析师", "结合四维分析锁定阶段性主线板块"),
    "index_impact": ("指数影响分析师", "反推板块主线对各指数的差异化影响"),
    "index_bull_bear": ("多空辩论", "多头与空头研究员进行正反辩论"),
    "index_manager": ("研究裁判", "综合判断并给出指数强弱排序"),
    "index_trader": ("指数交易员", "制定期货/期权交易策略"),
    "index_risk": ("风险辩论", "激进/保守/中性三方风险分析师辩论"),
    "index_risk_manager": ("风险裁判", "做出最终风控决策"),
}

PIPELINE_STAGES = [
    {"id": "tech", "name": "指数技术面分析师", "state_field": "index_technical_report", "order": 0},
    {"id": "sentiment", "name": "资金情绪分析师", "state_field": "index_sentiment_report", "order": 0},
    {"id": "macro", "name": "宏观政策分析师", "state_field": "macro_policy_report", "order": 0},
    {"id": "valuation", "name": "指数估值分析师", "state_field": "index_valuation_report", "order": 0},
    {"id": "sector", "name": "板块主线分析师", "state_field": "sector_theme_report", "order": 1},
    {"id": "impact", "name": "指数影响分析师", "state_field": "index_impact_report", "order": 2},
    {"id": "debate", "name": "多空辩论", "state_field": "index_debate_state", "order": 3},
    {"id": "manager", "name": "研究裁判", "state_field": "index_investment_plan", "order": 4},
    {"id": "trader", "name": "指数交易员", "state_field": "index_trading_plan", "order": 5},
    {"id": "risk", "name": "风险辩论", "state_field": "index_risk_debate_state", "order": 6},
    {"id": "risk_manager", "name": "风险裁判", "state_field": "final_index_decision", "order": 7},
]


class IndexPredictionService:
    def __init__(self):
        self.collection_name = "index_predictions"

    def _get_progress_tracker(self, task_id: str):
        from app.services.redis_progress_tracker import RedisProgressTracker
        return RedisProgressTracker(
            task_id=task_id,
            total_steps=len(STEP_MAP),
            research_depth="标准",
        )

    def _progress_callback(self, task_id: str):
        import time as _time
        start_time = _time.time()
        completed_fields = set()
        stage_times = {}

        def _build_pipeline_status(output: dict):
            now = _time.time()
            elapsed = now - start_time
            stages = []
            completed_count = 0

            for s in PIPELINE_STAGES:
                field = s["state_field"]
                val = output.get(field)
                done = val is not None and (isinstance(val, str) and val.strip()) or (isinstance(val, dict) and val)

                if done and field not in completed_fields:
                    completed_fields.add(field)
                    stage_times[field] = round(elapsed, 1)
                    done = True

                t = stage_times.get(field, 0)

                if done:
                    stages.append({"id": s["id"], "name": s["name"], "status": "completed", "time": t})
                    completed_count += 1
                else:
                    if s["order"] == 0:
                        status = "running" if not done else "pending"
                    else:
                        prev_stages = [p for p in PIPELINE_STAGES if p["order"] < s["order"]]
                        all_prev_done = all(
                            output.get(p["state_field"]) or p["state_field"] in completed_fields
                            for p in prev_stages
                        )
                        if all_prev_done and not done:
                            status = "running"
                        else:
                            status = "pending"
                    stages.append({"id": s["id"], "name": s["name"], "status": status, "time": t})

            total = len(PIPELINE_STAGES)
            progress = int(completed_count / total * 100) if total else 0

            return {
                "type": "pipeline_status",
                "stages": stages,
                "progress": progress,
                "elapsed_seconds": round(elapsed, 1),
            }

        def callback(output: dict):
            if not isinstance(output, dict):
                return
            payload = _build_pipeline_status(output)
            import json as _json
            try:
                from app.services.redis_progress_tracker import RedisProgressTracker
                tracker = RedisProgressTracker(task_id=task_id, total_steps=len(PIPELINE_STAGES), research_depth="标准")
                tracker.update_progress(payload["progress"])
            except Exception:
                pass
            try:
                import redis as _redis
                r = _redis.Redis(host="localhost", port=6379, password="tradingagents123", decode_responses=True)
                r.setex(f"ip_pipeline:{task_id}", 1800, _json.dumps(payload, ensure_ascii=False))
            except Exception:
                pass

        return callback

    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            import redis as _redis, json as _json
            r = _redis.Redis(host="localhost", port=6379, password="tradingagents123", decode_responses=True)
            raw = r.get(f"ip_pipeline:{task_id}")
            if raw:
                return _json.loads(raw)
        except Exception:
            pass
        try:
            from app.services.redis_progress_tracker import get_progress_by_id
            return get_progress_by_id(task_id)
        except Exception:
            return None

    async def _get_collection(self):
        from app.core.database import get_mongo_db
        db = get_mongo_db()
        return db[self.collection_name]

    async def start_prediction(self, user_id: str, request: Dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        depth = request.get("research_depth", "标准")
        depth_cfg = DEPTH_MAP.get(depth, DEPTH_MAP["标准"])

        doc = {
            "task_id": task_id,
            "user_id": user_id,
            "expectation_id": request.get("expectation_id", ""),
            "target_indices": request.get("target_indices", []),
            "research_depth": depth,
            "selected_analysts": request.get("selected_analysts", []),
            "status": "pending",
            "progress": 0,
            "result": None,
            "error": None,
            "created_at": now_tz(),
            "updated_at": now_tz(),
        }
        collection = await self._get_collection()
        await collection.insert_one(doc)

        asyncio.create_task(self._execute_prediction(task_id, user_id, request, depth_cfg))
        return task_id

    async def _execute_prediction(self, task_id: str, user_id: str, request: Dict[str, Any], depth_cfg: dict):
        collection = await self._get_collection()
        try:
            await collection.update_one(
                {"task_id": task_id},
                {"$set": {"status": "running", "updated_at": now_tz()}}
            )

            user_expectations = await self._load_expectations(
                request.get("expectation_id"), user_id
            )
            target_indices = request.get("target_indices", [
                "000016.SH", "000300.SH", "000905.SH", "000852.SH", "000688.SH", "399006.SZ"
            ])
            target_indices_str = ", ".join(target_indices)

            analysis_date = request.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))

            from tradingagents.graph.index_prediction_graph import IndexPredictionGraph

            import os as _os
            dashscope_api_key = _os.environ.get("DASHSCOPE_API_KEY", "")
            try:
                db = await self._get_collection()
                db_raw = db.database
                sys_cfg = await db_raw["system_configs"].find_one({"is_active": True})
                if sys_cfg:
                    llm_configs = sys_cfg.get("llm_configs", sys_cfg.get("llm_config", []))
                    for llm in llm_configs:
                        provider = llm.get("provider", llm.get("provider_name", ""))
                        if "dashscope" in str(provider).lower() or "百炼" in str(provider):
                            k = llm.get("api_key", "")
                            if k and len(k) > 20:
                                dashscope_api_key = k
                                break
            except Exception:
                pass

            config = {
                "max_debate_rounds": depth_cfg.get("debate_rounds", 1),
                "max_risk_discuss_rounds": depth_cfg.get("risk_rounds", 1),
                "memory_enabled": depth_cfg.get("memory_enabled", False),
                "online_tools": True,
                "llm_provider": "dashscope",
                "DASHSCOPE_API_KEY": dashscope_api_key,
                "quick_think_llm": request.get("quick_analysis_model", "qwen-plus"),
                "deep_think_llm": request.get("deep_analysis_model", "qwen-max"),
                "quick_model_config": {
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "timeout": 180,
                },
                "deep_model_config": {
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "timeout": 300,
                },
                "progress_callback": self._progress_callback(task_id),
            }

            graph = IndexPredictionGraph(debug=False, config=config)

            loop = asyncio.get_event_loop()
            elapsed, final_state = await loop.run_in_executor(
                None, graph.propagate,
                user_expectations, target_indices_str, analysis_date,
            )

            result = {
                "final_index_decision": final_state.get("final_index_decision", ""),
                "index_trading_plan": final_state.get("index_trading_plan", ""),
                "index_investment_plan": final_state.get("index_investment_plan", ""),
                "index_technical_report": final_state.get("index_technical_report", ""),
                "index_sentiment_report": final_state.get("index_sentiment_report", ""),
                "macro_policy_report": final_state.get("macro_policy_report", ""),
                "index_valuation_report": final_state.get("index_valuation_report", ""),
                "sector_theme_report": final_state.get("sector_theme_report", ""),
                "index_impact_report": final_state.get("index_impact_report", ""),
            }

            await collection.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": "completed",
                    "progress": 100,
                    "result": result,
                    "elapsed_seconds": elapsed,
                    "updated_at": now_tz(),
                }}
            )
            logger.info(f"Index prediction completed for task {task_id} in {elapsed:.1f}s")
        except Exception as e:
            import traceback as _tb
            error_str = str(e)
            if "Arrearage" in error_str or "overdue" in error_str.lower():
                error_str = "DashScope账户欠费，请登录阿里云百炼控制台充值后重试"
            logger.error(f"Index prediction failed for task {task_id}: {e}\n{_tb.format_exc()}")
            await collection.update_one(
                {"task_id": task_id},
                {"$set": {"status": "failed", "error": error_str, "updated_at": now_tz()}}
            )

    async def _load_expectations(self, expectation_id: str, user_id: str) -> str:
        if not expectation_id:
            return "用户未提供预期，请基于公开数据自主分析"
        try:
            from app.services.expectation_service import ExpectationService
            svc = ExpectationService()
            exp = await svc.get_by_id(expectation_id, user_id)
            if not exp:
                return "用户未提供预期，请基于公开数据自主分析"
            content = exp.get("content", {})
            if isinstance(content, str):
                return str(content)
            parts = []
            if content.get("policy_long_term"):
                parts.append(f"长期政策方向: {content['policy_long_term']}")
            if content.get("policy_medium_term"):
                parts.append(f"中期宏观政策: {content['policy_medium_term']}")
            if content.get("policy_short_term"):
                parts.append(f"短期政策/事件: {content['policy_short_term']}")
            if content.get("liquidity_assessment"):
                parts.append(f"流动性判断: {content['liquidity_assessment']}")
            if content.get("economic_phase"):
                parts.append(f"经济周期: {content['economic_phase']} - {content.get('cycle_detail', '')}")
            if content.get("market_trend"):
                parts.append(f"市场大势: {content['market_trend']} - {content.get('market_phase_detail', '')}")
            for sv in content.get("sector_views", []):
                parts.append(f"板块观点: {sv['sector_name']} - {sv['thesis']} (信心度: {sv['confidence']})")
            for cs in content.get("custom_sections", []):
                parts.append(f"{cs['title']}: {cs['content']}")
            return "\n".join(parts)
        except Exception as e:
            logger.warning(f"Failed to load expectations: {e}")
            return "用户预期加载失败，请基于公开数据自主分析"

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        collection = await self._get_collection()
        doc = await collection.find_one({"task_id": task_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        return None

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.get_task_status(task_id)
        if doc and doc.get("status") == "completed":
            return doc.get("result")
        return None

    async def get_history(self, user_id: str, skip: int = 0, limit: int = 20) -> list:
        collection = await self._get_collection()
        cursor = collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def get_indices_metadata(self) -> list:
        from tradingagents.dataflows.providers.china.index_data import TARGET_INDICES
        return [
            {"code": k, "name": v["name"], "display": v["display"],
             "market": v["market"],
             "futures": {"000016.SH": "IH", "000300.SH": "IF", "000905.SH": "IC", "000852.SH": "IM"}.get(k, "-")}
            for k, v in TARGET_INDICES.items()
        ]

    async def get_sectors(self) -> list:
        try:
            from tradingagents.dataflows.providers.china.sector_data import get_sector_data_provider
            provider = get_sector_data_provider()
            return provider.get_sw_sector_list()
        except Exception as e:
            logger.warning(f"Failed to get sectors: {e}")
            return []
    async def list_all_tasks(self, user_id: str, status: Optional[str] = None, skip: int = 0, limit: int = 50):
        collection = await self._get_collection()
        query: Dict[str, Any] = {"user_id": user_id}
        if status:
            query["status"] = status
        total = await collection.count_documents(query)
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        tasks = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            tasks.append(doc)
        return tasks, total

    async def cancel_task(self, task_id: str) -> bool:
        collection = await self._get_collection()
        doc = await collection.find_one({"task_id": task_id})
        if not doc:
            return False
        result = await collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "cancelled", "updated_at": now_tz()}},
        )
        return result.modified_count > 0

    async def delete_task(self, task_id: str) -> bool:
        collection = await self._get_collection()
        result = await collection.delete_one({"task_id": task_id})
        return result.deleted_count > 0

    async def mark_task_failed(self, task_id: str) -> bool:
        collection = await self._get_collection()
        result = await collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "failed", "error": "用户手动标记为失败", "updated_at": now_tz()}},
        )
        return result.modified_count > 0

    async def retry_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.get_task_status(task_id)
        if not doc:
            return None
        request_data = {
            "expectation_id": doc.get("expectation_id", ""),
            "target_indices": doc.get("target_indices", [
                "000016.SH", "000300.SH", "000905.SH", "000852.SH", "000688.SH", "399006.SZ"
            ]),
            "research_depth": doc.get("research_depth", "标准"),
            "selected_analysts": doc.get("selected_analysts", ["tech", "sentiment", "macro", "valuation"]),
            "quick_analysis_model": doc.get("quick_analysis_model"),
            "deep_analysis_model": doc.get("deep_analysis_model"),
            "analysis_date": doc.get("analysis_date"),
        }
        new_task_id = await self.start_prediction(user_id, request_data)
        return {"task_id": new_task_id, "status": "pending"}
