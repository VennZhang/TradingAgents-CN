def create_index_neutral_debater(llm):
    def neutral_node(state) -> dict:
        risk_state = state.get("index_risk_debate_state", {
            "risky_history": "", "safe_history": "", "neutral_history": "",
            "history": "", "latest_speaker": "",
            "current_risky_response": "", "current_safe_response": "",
            "current_neutral_response": "", "judge_decision": "", "count": 0,
        })

        trading_plan = state.get("index_trading_plan", "")
        investment_plan = state.get("index_investment_plan", "")

        prompt = f"""你是一位中性的风险分析师。在激进和保守之间寻找平衡的风险评估。

## 交易计划
{trading_plan[:1500]}

## 研究结论
{investment_plan[:1000]}

## 激进观点
{risk_state.get('current_risky_response', '')[:800]}

## 保守观点
{risk_state.get('current_safe_response', '')[:800]}

## 讨论历史
{risk_state.get('history', '')}

请给出平衡的风险判断：
1. 哪些风险被高估/低估了？
2. 风险收益比是否合理？
3. 是否有改进方案可以同时满足风险管理和收益需求？
4. 建议的风险预算分配（各指数/策略的风险敞口上限）"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        new_state = {
            "risky_history": risk_state.get("risky_history", ""),
            "safe_history": risk_state.get("safe_history", ""),
            "neutral_history": risk_state.get("neutral_history", "") + f"\n中性: {content}",
            "history": risk_state.get("history", "") + f"\n中性: {content}",
            "latest_speaker": "neutral",
            "current_risky_response": risk_state.get("current_risky_response", ""),
            "current_safe_response": risk_state.get("current_safe_response", ""),
            "current_neutral_response": content,
            "judge_decision": "",
            "count": risk_state.get("count", 0) + 1,
        }
        return {"index_risk_debate_state": new_state}

    return neutral_node
