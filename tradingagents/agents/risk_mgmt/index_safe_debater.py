def create_index_safe_debater(llm):
    def safe_node(state) -> dict:
        risk_state = state.get("index_risk_debate_state", {
            "risky_history": "", "safe_history": "", "neutral_history": "",
            "history": "", "latest_speaker": "",
            "current_risky_response": "", "current_safe_response": "",
            "current_neutral_response": "", "judge_decision": "", "count": 0,
        })

        trading_plan = state.get("index_trading_plan", "")
        investment_plan = state.get("index_investment_plan", "")

        prompt = f"""你是一位保守的风险分析师。评估当前指数交易计划的风险控制是否充分。

## 交易计划
{trading_plan[:1500]}

## 研究结论
{investment_plan[:1000]}

## 激进分析师的风险评估
{risk_state.get('current_risky_response', '')[:1000]}

## 讨论历史
{risk_state.get('history', '')}

请从保守角度分析：
1. 仓位是否过高？合理的安全仓位是多少？
2. 止损设置是否过于宽松？
3. 是否有被忽略的下行风险？
4. 是否需要更严格的对冲保护？
5. 最大回撤的合理预期是多少？"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        new_state = {
            "risky_history": risk_state.get("risky_history", ""),
            "safe_history": risk_state.get("safe_history", "") + f"\n保守: {content}",
            "neutral_history": risk_state.get("neutral_history", ""),
            "history": risk_state.get("history", "") + f"\n保守: {content}",
            "latest_speaker": "safe",
            "current_risky_response": risk_state.get("current_risky_response", ""),
            "current_safe_response": content,
            "current_neutral_response": risk_state.get("current_neutral_response", ""),
            "judge_decision": "",
            "count": risk_state.get("count", 0) + 1,
        }
        return {"index_risk_debate_state": new_state}

    return safe_node
