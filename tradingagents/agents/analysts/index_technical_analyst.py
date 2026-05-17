from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_index_technical_analyst(llm, toolkit):
    def index_technical_node(state) -> dict:
        current_date = state.get("trade_date", "")
        user_expectations = state.get("user_expectations", "")
        target_indices = state.get("target_indices", "")

        tools = [
            toolkit.get_index_data,
        ]

        system_message = (
            "你是一位资深的指数技术分析师，专注于A股六大宽基指数的技术面分析。\n"
            "你的任务是对每个指数进行全面的技术面评估，包括：\n"
            "1. 趋势分析（日线/周线级别的多空趋势判断）\n"
            "2. 关键技术位（支撑位、阻力位）\n"
            "3. 技术指标评估（均线系统、MACD、RSI、布林带）\n"
            "4. 量价关系分析\n\n"
            "请为每个目标指数给出技术面评分（1-10分）、趋势方向（看多/看空/震荡）和核心判断理由。\n"
            "最后给出六大指数的技术面强弱排序。"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}\n\n"
             "当前日期: {current_date}\n"
             "目标指数: {target_indices}\n\n"
             "## 用户预期（作为分析前提）\n"
             "{user_expectations}\n\n"
             "可用的数据工具: {tool_names}\n"
             "请使用 get_index_data 工具获取各指数K线数据进行分析。"),
            MessagesPlaceholder(variable_name="messages"),
        ])
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(target_indices=target_indices)
        prompt = prompt.partial(user_expectations=user_expectations)
        prompt = prompt.partial(tool_names="get_index_data")

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = result.content if hasattr(result, 'content') else ""

        count = state.get("tech_tool_call_count", 0) + 1
        return {
            "messages": [result],
            "index_technical_report": report,
            "tech_tool_call_count": count,
        }

    return index_technical_node
