from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_macro_policy_analyst(llm, toolkit):
    def macro_policy_node(state) -> dict:
        current_date = state.get("trade_date", "")
        user_expectations = state.get("user_expectations", "")

        tools = [
            toolkit.get_macro_news,
            toolkit.get_index_data,
        ]

        system_message = (
            "你是一位宏观政策分析专家，专注于宏观经济政策和大事件的解读。\n"
            "你的任务包括：\n"
            "1. 宏观经济数据解读：GDP、CPI、PMI、货币供应量等关键指标\n"
            "2. 货币政策分析：央行政策取向、利率、降准降息预期\n"
            "3. 财政政策分析：产业政策、财政支出、专项债等\n"
            "4. 全球宏观事件：地缘政治、贸易摩擦、海外央行政策外溢效应\n"
            "5. 经济周期定位：当前处于复苏/繁荣/衰退/萧条哪个阶段\n\n"
            "请结合用户的主观预期（如有），给出宏观层面的政策方向判断和经济环境评估。\n"
            "⚠️ 用户已填写的预期作为分析前提，不要质疑。"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}\n\n"
             "当前日期: {current_date}\n\n"
             "## 用户主观预期\n{user_expectations}\n\n"
             "可用的数据工具: {tool_names}\n"
             "请使用 get_macro_news 获取宏观数据和政策新闻，必要时使用 get_index_data 验证政策对市场的影响。"),
            MessagesPlaceholder(variable_name="messages"),
        ])
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(user_expectations=user_expectations)
        prompt = prompt.partial(tool_names="get_macro_news, get_index_data")

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = result.content if hasattr(result, 'content') else ""

        count = state.get("macro_tool_call_count", 0) + 1
        return {
            "messages": [result],
            "macro_policy_report": report,
            "macro_tool_call_count": count,
        }

    return macro_policy_node
