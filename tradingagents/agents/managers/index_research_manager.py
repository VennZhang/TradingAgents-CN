def create_index_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        debate_state = state.get("index_debate_state", {})
        technical = state.get("index_technical_report", "")
        sentiment = state.get("index_sentiment_report", "")
        macro = state.get("macro_policy_report", "")
        valuation = state.get("index_valuation_report", "")
        sector_theme = state.get("sector_theme_report", "")
        index_impact = state.get("index_impact_report", "")

        curr_situation = (
            f"## 技术面\n{technical[:600]}\n## 情绪\n{sentiment[:600]}\n"
            f"## 宏观\n{macro[:600]}\n## 估值\n{valuation[:600]}\n"
            f"## 板块主线\n{sector_theme[:600]}\n## 指数影响\n{index_impact[:600]}"
        )

        past_memories = ""
        try:
            past = memory.get_memories(curr_situation, n_matches=2)
            past_memories = f"\n## 历史参考\n{past}\n"
        except Exception:
            pass

        prompt = f"""你是一位权威的指数研究裁判。多空双方已完成辩论，请做出最终综合判断。

{past_memories}

## 多空辩论记录
{debate_state.get('history', '无辩论记录')}

## 全部分析报告
{curr_situation}

请给出以下内容：
1. 多空观点评价：双方核心论点的合理性和弱点
2. 综合判断：基于全部分析，对六大指数的方向性判断
3. 指数强弱排序：从最看好到最谨慎的排序
4. 关键风险因素清单
5. 建议仓位配置：各指数的大致比例建议"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        new_debate_state = dict(debate_state)
        new_debate_state["judge_decision"] = content

        return {
            "index_debate_state": new_debate_state,
            "index_investment_plan": content,
        }

    return research_manager_node
