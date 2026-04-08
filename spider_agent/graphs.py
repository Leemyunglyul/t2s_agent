from langgraph.graph import StateGraph, END
import logging

from .state import AgentState
from .nodes import (
    query_analysis_node,
    schema_linking_node,
    data_profiling_node,
    sql_writer_node,      # 💡 작성자 노드
    sql_modifier_node,    # 💡 수정자 노드
    execution_node,
    critic_node 
)

logger = logging.getLogger("langgraph_agent")
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def route_after_execution(state: AgentState):
    if state.get("has_error"):
        if state.get("retry_count", 0) >= state.get("max_steps", 20):
            return "end"
        return "retry"
    else:
        if state.get("is_final_answer"):
            return "critic"
        return "retry"

def route_after_critic(state: AgentState):
    if state.get("has_error"):
        if state.get("retry_count", 0) >= state.get("max_steps", 20):
            return "end"
        return "retry"
    return "end"

def build_agent_graph():
    workflow = StateGraph(AgentState)

    # 💡 노드 등록 (Writer, Modifier 분리)
    workflow.add_node("Query_Analysis", query_analysis_node)
    workflow.add_node("Schema_Linking", schema_linking_node)
    workflow.add_node("Data_Profiling", data_profiling_node)
    workflow.add_node("SQL_Writer", sql_writer_node)
    workflow.add_node("SQL_Modifier", sql_modifier_node)
    workflow.add_node("Execution", execution_node)
    workflow.add_node("Critic", critic_node)

    workflow.set_entry_point("Query_Analysis")
    workflow.add_edge("Query_Analysis", "Schema_Linking")
    workflow.add_edge("Schema_Linking", "Data_Profiling")
    workflow.add_edge("Data_Profiling", "SQL_Writer")      # 💡 Profiling 후 Writer로 이동
    workflow.add_edge("SQL_Writer", "Execution")           # 💡 Writer 작성 후 Execution으로 이동
    workflow.add_edge("SQL_Modifier", "Execution")         # 💡 Modifier 수정 후 Execution으로 이동

    workflow.add_conditional_edges(
        "Execution",
        route_after_execution,
        {
            "critic": "Critic",
            "retry": "SQL_Modifier",  # 💡 에러 발생 시 Modifier에게 전달
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "Critic",
        route_after_critic,
        {
            "retry": "SQL_Modifier",  # 💡 비평가 반려 시 Modifier에게 전달
            "end": END
        }
    )

    app = workflow.compile()
    return app