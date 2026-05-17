def create_index_risky_debater(llm):
    def risky_node(state) -> dict:
        risk_state = state.get("index_risk_debate_state", {
            "risky_history": "", "safe_history": "", "neutral_history": "",
            "history": "", "latest_speaker": "",
            "current_risky_response": "", "current_safe_response": "",
            "current_neutral_response": "", "judge_decision": "", "count": 0,
        })

        trading_plan = state.get("index_trading_plan", "")
        investment_plan = state.get("index_investment_plan", "")

        prompt = f"""你是一位激进的风险分析师。评估当前指数交易计划的潜在风险。

## 交易计划
{trading_plan[:1500]}

## 研究结论
{investment_plan[:1000]}

## 讨论历史
{risk_state.get('history', '')}

请聚焦以下风险维度：
1. 杠杆风险：期货保证金压力、爆仓风险
2. 方向性风险：多指数同向波动的相关性风险
3. 尾部风险：熔断、大幅跳空等极端事件
4. 基差风险：展期成本和基差波动
5. 流动性风险：远月合约的流动性问题

请以最激进的风险视角进行分析。"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        new_state = {
            "risky_history": risk_state.get("risky_history", "") + f"\n激进: {content}",
            "safe_history": risk_state.get("safe_history", ""),
            "neutral_history": risk_state.get("neutral_history", ""),
            "history": risk_state.get("history", "") + f"\n激进: {content}",
            "latest_speaker": "risky",
            "current_risky_response": content,
            "current_safe_response": risk_state.get("current_safe_response", ""),
            "current_neutral_response": risk_state.get("current_neutral_response", ""),
            "judge_decision": "",
            "count": risk_state.get("count", 0) + 1,
        }
        return {"index_risk_debate_state": new_state}

    return risky_node
