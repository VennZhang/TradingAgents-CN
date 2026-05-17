from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_sector_theme_analyst(llm, toolkit):
    def sector_theme_node(state) -> dict:
        current_date = state.get("trade_date", "")
        user_expectations = state.get("user_expectations", "")
        technical = state.get("index_technical_report", "")
        sentiment = state.get("index_sentiment_report", "")
        macro = state.get("macro_policy_report", "")
        valuation = state.get("index_valuation_report", "")

        tools = [
            toolkit.get_sector_performance,
            toolkit.get_sector_list,
        ]

        system_message = (
            "你是一位板块主线分析师，负责从多维分析报告中锁定阶段性主线板块。\n"
            "你的任务：\n"
            "1. 结合指数技术面、资金情绪、宏观政策和估值四份报告\n"
            "2. 识别当前市场的3-5个主线板块\n"
            "3. 分析每个主线板块的驱动逻辑（政策驱动/周期驱动/超跌反弹/结构性增长）\n"
            "4. 判断主线板块的持续性（短期/中期/长期）\n"
            "5. 考虑用户预期的板块偏好（如有）\n\n"
            "输出格式：明确列出主线板块名称、驱动逻辑、持续性判断和置信度。"
        )

        context = (
            f"## 指数技术面分析\n{technical[:1000]}\n\n"
            f"## 资金情绪分析\n{sentiment[:1000]}\n\n"
            f"## 宏观政策分析\n{macro[:1000]}\n\n"
            f"## 指数估值分析\n{valuation[:1000]}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}\n\n"
             "当前日期: {current_date}\n\n"
             "## 四维分析报告摘要\n{context}\n\n"
             "## 用户板块偏好\n{user_expectations}\n\n"
             "可用的数据工具: {tool_names}\n"
             "请使用 get_sector_performance 和 get_sector_list 获取板块数据。"),
            MessagesPlaceholder(variable_name="messages"),
        ])
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(context=context)
        prompt = prompt.partial(user_expectations=user_expectations)
        prompt = prompt.partial(tool_names="get_sector_performance, get_sector_list")

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = result.content if hasattr(result, 'content') else ""

        count = state.get("sector_tool_call_count", 0) + 1
        return {
            "messages": [result],
            "sector_theme_report": report,
            "sender": "板块主线分析师",
            "sector_tool_call_count": count,
        }

    return sector_theme_node
