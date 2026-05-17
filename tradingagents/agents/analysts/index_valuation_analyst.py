from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_index_valuation_analyst(llm, toolkit):
    def index_valuation_node(state) -> dict:
        current_date = state.get("trade_date", "")
        target_indices = state.get("target_indices", "")

        tools = [
            toolkit.get_index_valuation_data,
            toolkit.get_index_constituents,
            toolkit.get_index_sector_weights,
        ]

        system_message = (
            "你是一位指数估值分析师，专注于宽基指数的估值水平和结构性分析。\n"
            "你的任务包括：\n"
            "1. 估值水平：各指数PE/PB当前值、历史分位（近5年）\n"
            "2. 风险溢价（ERP）：相对于无风险利率的股权风险溢价\n"
            "3. 股息率：各指数股息率水平和趋势\n"
            "4. 板块结构：各指数的行业权重分布、市值结构\n"
            "5. 估值比较：跨指数的估值横向比较、大盘vs中小盘估值差异\n\n"
            "请给出各指数的贵贱判断、安全边际和结构性风险。"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}\n\n"
             "当前日期: {current_date}\n"
             "目标指数: {target_indices}\n\n"
             "可用的数据工具: {tool_names}\n"
             "请使用 get_index_valuation_data 获取估值数据，\n"
             "使用 get_index_constituents 了解成分结构，\n"
             "使用 get_index_sector_weights 分析板块权重。"),
            MessagesPlaceholder(variable_name="messages"),
        ])
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(target_indices=target_indices)
        prompt = prompt.partial(tool_names="get_index_valuation_data, get_index_constituents, get_index_sector_weights")

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = result.content if hasattr(result, 'content') else ""

        count = state.get("valuation_tool_call_count", 0) + 1
        return {
            "messages": [result],
            "index_valuation_report": report,
            "valuation_tool_call_count": count,
        }

    return index_valuation_node
