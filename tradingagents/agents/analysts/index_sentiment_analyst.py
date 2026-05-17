from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_index_sentiment_analyst(llm, toolkit):
    def index_sentiment_node(state) -> dict:
        current_date = state.get("trade_date", "")
        target_indices = state.get("target_indices", "")

        tools = [
            toolkit.get_futures_sentiment_data,
            toolkit.get_fund_flow_data,
            toolkit.get_margin_data,
        ]

        system_message = (
            "你是一位资金情绪分析师，专注于A股市场的资金流向和情绪指标分析。\n"
            "你的任务包括：\n"
            "1. 期货市场情绪：分析股指期货持仓量变化、基差、升贴水结构\n"
            "2. 资金流向：北向资金、ETF资金流、主力资金动向\n"
            "3. 融资融券：两融余额变化、杠杆情绪判断\n"
            "4. 市场情绪综合指标：恐慌/贪婪指数、成交量比率\n\n"
            "请判断当前市场整体情绪是偏多、偏空还是中性，并给出量化依据。"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}\n\n"
             "当前日期: {current_date}\n"
             "目标指数: {target_indices}\n\n"
             "可用的数据工具: {tool_names}\n"
             "请使用工具获取资金流、期货和融资融券数据进行分析。"),
            MessagesPlaceholder(variable_name="messages"),
        ])
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(target_indices=target_indices)
        prompt = prompt.partial(tool_names="get_futures_sentiment_data, get_fund_flow_data, get_margin_data")

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = result.content if hasattr(result, 'content') else ""

        count = state.get("sentiment_tool_call_count", 0) + 1
        return {
            "messages": [result],
            "index_sentiment_report": report,
            "sentiment_tool_call_count": count,
        }

    return index_sentiment_node
