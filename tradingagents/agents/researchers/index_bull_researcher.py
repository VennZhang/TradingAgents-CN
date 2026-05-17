def create_index_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        debate_state = state.get("index_debate_state", {
            "bull_history": "", "bear_history": "", "history": "",
            "current_response": "", "judge_decision": "", "count": 0,
        })

        invest_plan = state.get("index_impact_report", "")
        technical = state.get("index_technical_report", "")
        sentiment = state.get("index_sentiment_report", "")
        macro = state.get("macro_policy_report", "")
        valuation = state.get("index_valuation_report", "")
        sector_theme = state.get("sector_theme_report", "")

        curr_situation = f"## 各项分析报告\n技术面: {technical[:500]}\n情绪: {sentiment[:500]}\n宏观: {macro[:500]}\n估值: {valuation[:500]}\n板块: {sector_theme[:500]}\n指数影响: {invest_plan[:500]}"

        past_memories = ""
        try:
            past = memory.get_memories(curr_situation, n_matches=2)
            past_memories = f"\n## 历史相关记忆\n{past}\n"
        except Exception:
            pass

        prompt = f"""你是一位激进的指数多头研究员。你的职责是构建最有力的做多论据。

{past_memories}

## 当前背景
{curr_situation}

## 辩论历史
{debate_state.get('history', '')}

## 当前空头观点
{debate_state.get('bear_history', '')[:1000]}

请从以下角度论证做多：
1. 宏观政策面的利多因素
2. 资金面和情绪面的积极信号
3. 板块主线的持续性逻辑
4. 估值的安全边际
5. 技术面的底部/突破信号

请针对空头观点进行有力反驳。聚焦于六大指数的整体方向性判断。"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        new_state = {
            "bull_history": debate_state.get("bull_history", "") + f"\n多头: {content}",
            "bear_history": debate_state.get("bear_history", ""),
            "history": debate_state.get("history", "") + f"\n多头: {content}",
            "current_response": content,
            "judge_decision": "",
            "count": debate_state.get("count", 0) + 1,
        }
        return {"index_debate_state": new_state}

    return bull_node
