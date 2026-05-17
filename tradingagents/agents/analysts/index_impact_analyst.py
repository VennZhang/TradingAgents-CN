from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_index_impact_analyst(llm, toolkit):
    def index_impact_node(state) -> dict:
        current_date = state.get("trade_date", "")
        target_indices = state.get("target_indices", "")
        user_expectations = state.get("user_expectations", "")
        technical = state.get("index_technical_report", "")
        sentiment = state.get("index_sentiment_report", "")
        macro = state.get("macro_policy_report", "")
        valuation = state.get("index_valuation_report", "")
        sector_theme = state.get("sector_theme_report", "")

        tools = [
            toolkit.get_index_constituents,
            toolkit.get_index_sector_weights,
        ]

        system_message = (
            "你是一位指数影响分析师，核心任务是反推板块主线对各指数的差异化影响。\n"
            "你的工作分两步：\n\n"
            "第一步：权重映射\n"
            "- 获取六大指数的成分股和板块权重数据\n"
            "- 计算每个主线板块在各指数中的暴露度（板块权重 × 板块预期涨幅）\n\n"
            "第二步：综合排序\n"
            "- 汇总各板块拉动效应\n"
            "- 考虑市场风格（大盘/小盘、价值/成长）对指数差异的影响\n"
            "- 给出六大指数的预期强弱排序（从最强到最弱）\n\n"
            "输出格式：\n"
            "1. 板块-权重映射表（每个主线板块在各指数中的权重）\n"
            "2. 拉动效应分析（每个指数受主线板块的综合影响）\n"
            "3. 六大指数预期强弱排序（含排序理由）"
        )

        context = (
            f"## 指数技术面\n{technical[:800]}\n\n"
            f"## 资金情绪\n{sentiment[:800]}\n\n"
            f"## 宏观政策\n{macro[:800]}\n\n"
            f"## 指数估值\n{valuation[:800]}\n\n"
            f"## 板块主线\n{sector_theme[:1000]}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}\n\n"
             "当前日期: {current_date}\n"
             "目标指数: {target_indices}\n\n"
             "## 全部分析报告\n{context}\n\n"
             "## 用户预期\n{user_expectations}\n\n"
             "可用的数据工具: {tool_names}\n"
             "请使用 get_index_constituents 和 get_index_sector_weights 获取权重数据。"),
            MessagesPlaceholder(variable_name="messages"),
        ])
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(target_indices=target_indices)
        prompt = prompt.partial(context=context)
        prompt = prompt.partial(user_expectations=user_expectations)
        prompt = prompt.partial(tool_names="get_index_constituents, get_index_sector_weights")

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = result.content if hasattr(result, 'content') else ""

        count = state.get("impact_tool_call_count", 0) + 1
        return {
            "messages": [result],
            "index_impact_report": report,
            "sender": "指数影响分析师",
            "impact_tool_call_count": count,
        }

    return index_impact_node
