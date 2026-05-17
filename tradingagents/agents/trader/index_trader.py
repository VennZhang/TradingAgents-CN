import functools


def create_index_trader(llm, memory):
    def trader_node(state, name):
        investment_plan = state.get("index_investment_plan", "")
        index_impact = state.get("index_impact_report", "")
        user_expectations = state.get("user_expectations", "")

        curr_situation = (
            f"## 研究裁判的结论\n{investment_plan[:1500]}\n\n"
            f"## 指数影响分析\n{index_impact[:1000]}"
        )

        past_memories = ""
        try:
            past = memory.get_memories(curr_situation, n_matches=2)
            past_memories = f"\n## 历史交易记忆\n{past}\n"
        except Exception:
            pass

        prompt = f"""你是一位专业的指数期货/期权交易员。基于分析报告，制定具体交易策略。

{past_memories}

## 分析背景
{curr_situation}

## 用户预期
{user_expectations}

请制定具体的指数期货/期权交易计划：
1. 核心策略：做多/做空哪些指数？配对交易方案？
2. 合约选择：IH(上证50)/IF(沪深300)/IC(中证500)/IM(中证1000)的具体配置
3. 仓位管理：各合约的保证金占比和风险敞口
4. 期权策略：针对最强/最弱指数的买Call/Put或价差组合
5. 止损止盈：具体的技术位止损和止盈目标
6. 展期策略：近月/远月合约的选择逻辑"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        return {
            "messages": [response],
            "index_trading_plan": content,
            "sender": name,
        }

    return functools.partial(trader_node, name="指数交易员")
