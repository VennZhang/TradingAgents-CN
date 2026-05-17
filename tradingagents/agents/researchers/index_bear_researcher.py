def create_index_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
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

        prompt = f"""你是一位保守的指数空头研究员。你的职责是构建最有力的做空或谨慎论据。

{past_memories}

## 当前背景
{curr_situation}

## 辩论历史
{debate_state.get('history', '')}

## 当前多头观点
{debate_state.get('bull_history', '')[:1000]}

请从以下角度论证做空/谨慎：
1. 宏观经济的下行风险
2. 政策预期的落空风险
3. 估值过高的泡沫风险
4. 资金流出的技术面风险
5. 全球地缘政治不确定性

请针对多头观点进行有力反驳。给出六大指数的风险排序。"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        new_state = {
            "bull_history": debate_state.get("bull_history", ""),
            "bear_history": debate_state.get("bear_history", "") + f"\n空头: {content}",
            "history": debate_state.get("history", "") + f"\n空头: {content}",
            "current_response": content,
            "judge_decision": "",
            "count": debate_state.get("count", 0) + 1,
        }
        return {"index_debate_state": new_state}

    return bear_node
