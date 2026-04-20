from langgraph.graph import StateGraph, END
import logging

from .state import AgentState
from .nodes import (
    keyword_extraction_node,
    query_planning_node,
    schema_linking_node,
    data_profiling_node,
    sql_writer_node,
    sql_modifier_node,
    execution_node,
    critic_node         # 💡 주석 해제 (비평가 복구)
)

logger = logging.getLogger("langgraph_agent")
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def route_after_execution(state: AgentState):
    if state.get("has_error"):
        if state.get("retry_count", 0) >= state.get("max_steps", 10):
            return "end"
        return "retry"
    else:
        if state.get("is_final_answer"):
            return "critic" # 💡 성공 시 바로 END가 아니라 Critic으로 넘김
        return "retry"

def route_after_critic(state: AgentState): # 💡 비평가 라우터 복구
    if state.get("has_error"):
        if state.get("retry_count", 0) >= state.get("max_steps", 10):
            return "end"
        return "retry" # 비평가가 반려하면 다시 Modifier로
    return "end" # 비평가가 통과시키면 최종 종료

def build_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("Keyword_Extraction", keyword_extraction_node)
    workflow.add_node("Schema_Linking", schema_linking_node)
    workflow.add_node("Data_Profiling", data_profiling_node)
    workflow.add_node("Query_Planning", query_planning_node)
    workflow.add_node("SQL_Writer", sql_writer_node)
    workflow.add_node("SQL_Modifier", sql_modifier_node)
    workflow.add_node("Execution", execution_node)
    workflow.add_node("Critic", critic_node) # 💡 노드 복구

    workflow.set_entry_point("Keyword_Extraction")
    workflow.add_edge("Keyword_Extraction", "Schema_Linking")
    workflow.add_edge("Schema_Linking", "Data_Profiling")
    workflow.add_edge("Data_Profiling", "Query_Planning") 
    workflow.add_edge("Query_Planning", "SQL_Writer")
    
    workflow.add_edge("SQL_Writer", "Execution")
    workflow.add_edge("SQL_Modifier", "Execution")

    workflow.add_conditional_edges(
        "Execution",
        route_after_execution,
        {
            "critic": "Critic",     # 💡 Execution 성공 -> Critic
            "retry": "SQL_Modifier",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "Critic",
        route_after_critic,
        {
            "retry": "SQL_Modifier", # 💡 Critic 반려 -> Modifier
            "end": END               # 💡 Critic 통과 -> END
        }
    )

    app = workflow.compile()
    return app