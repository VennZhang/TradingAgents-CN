def create_index_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:
        risk_state = state.get("index_risk_debate_state", {})
        trading_plan = state.get("index_trading_plan", "")
        investment_plan = state.get("index_investment_plan", "")

        curr_situation = (
            f"## 交易计划\n{trading_plan[:1000]}\n\n"
            f"## 研究结论\n{investment_plan[:800]}"
        )

        past_memories = ""
        try:
            past = memory.get_memories(curr_situation, n_matches=2)
            past_memories = f"\n## 历史风控记忆\n{past}\n"
        except Exception:
            pass

        prompt = f"""你是指数交易的风险管理裁判。三方风险分析师已完成辩论，请做出最终风险决策。

{past_memories}

## 风险辩论记录
{risk_state.get('history', '无辩论记录')}

## 交易方案
{trading_plan}

## 研究背景
{investment_plan}

请给出最终风控决策：
1. 总体风险评级：低/中/高/极高
2. 批准/调整/否决交易计划
3. 具体风控措施建议：
   - 仓位上限
   - 止损线
   - 对冲要求
   - 监控指标
4. 最大可接受损失金额
5. 应急预案（极端行情响应方案）"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        new_risk_state = dict(risk_state)
        new_risk_state["judge_decision"] = content

        return {
            "index_risk_debate_state": new_risk_state,
            "final_index_decision": content,
        }

    return risk_manager_node
