import json
import logging
import re
import sqlite3
import os
import glob
import threading
import csv
from typing import Dict, Any, Tuple

import sqlglot
from sqlglot import exp

from .llm import call_llm
from .state import AgentState
from .prompts import QUERY_ANALYSIS_SYSTEM, SCHEMA_LINKING_SYSTEM, SQL_GENERATION_SYSTEM, DATA_PROFILING_SYSTEM, CRITIC_SYSTEM_PROMPT
from .tools import llm_based_schema_linking

logger = logging.getLogger("langgraph_agent")

def clean_json_string(raw_string: str) -> str:
    match = re.search(r'\{.*\}', raw_string, re.DOTALL)
    if match:
        return match.group(0)
    return raw_string

def parse_llm_sql_output(response_text: str) -> Tuple[str, bool]:
    response_text = response_text.strip()
    
    try:
        clean_json = re.sub(r"^```json\s*|\s*```$", "", response_text, flags=re.IGNORECASE).strip()
        parsed_data = json.loads(clean_json, strict=False)
        
        if "Thought" in parsed_data:
            logger.info(f"[Thought]: {parsed_data['Thought']}")
            
        sql = parsed_data.get("SQL", "").strip()
        sql = re.sub(r"^```sql\s*|\s*```$", "", sql, flags=re.IGNORECASE).strip()
        
        action_type = parsed_data.get("Action_Type", "FINAL").upper()
        is_final = (action_type == "FINAL")
        logger.info(f"✨ [JSON 파싱 성공] {action_type} SQL 추출 완료!")
        return sql, is_final
    except json.JSONDecodeError:
        pass

    thought_match = re.search(r"\[Thought\]:\s*(.*?)(?=\[EXPLORE SQL\]:|\[FINAL SQL\]:|$)", response_text, re.DOTALL | re.IGNORECASE)
    if thought_match:
        logger.info(f"[Thought]:\n{thought_match.group(1).strip()}")

    if "[FINAL SQL]:" in response_text:
        raw_sql = response_text.split("[FINAL SQL]:", 1)[1].strip()
        sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_sql, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            sql = re.sub(r"^```sql\s*|\s*```$", "", raw_sql, flags=re.IGNORECASE).strip()
            
        logger.info("✨ [텍스트 태그 파싱 성공] FINAL SQL 추출 완료!")
        return sql, True
        
    elif "[EXPLORE SQL]:" in response_text:
        raw_sql = response_text.split("[EXPLORE SQL]:", 1)[1].strip()
        sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_sql, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            sql = re.sub(r"^```sql\s*|\s*```$", "", raw_sql, flags=re.IGNORECASE).strip()
            
        logger.info("🔍 [텍스트 태그 파싱 성공] EXPLORE SQL 추출 완료!")
        return sql, False
        
    logger.warning("🚨 태그 형식 누락! 정규식 강제 추출 시도.")
    sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip(), True
    elif response_text.upper().startswith(("SELECT", "WITH", "CREATE", "DROP", "PRAGMA")):
        return response_text, True
        
    return response_text, True 

def query_analysis_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Query Analysis (Planner) 실행 중...")
    
    question = state.get("question", "")
    if not question:
        logger.error("State에 'question'이 없습니다.")
        return {"has_error": True, "observation": "Missing question in state."}

    work_dir = state.get("working_dir", "")
    domain_rules = load_domain_rules(work_dir)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES & HINTS]\n{domain_rules}\n" if domain_rules else ""
    
    # Planner용 시스템 프롬프트에 도메인 룰 추가
    dynamic_planner_system = QUERY_ANALYSIS_SYSTEM + domain_prompt + "\nIMPORTANT: When creating the plan, remember to use DENSE_RANK for ties, ROW_NUMBER for global first terms, and avoid INNER JOINs for metrics."
    
    messages = [
        {"role": "system", "content": dynamic_planner_system},
        {"role": "user", "content": f"User Question: \"{question}\""}
    ]
    
    logger.info(f"질문 분석 요청: '{question}'")
    status, response = call_llm({
        "messages": messages,
        "temperature": 0.0,
        "response_mime_type": "application/json"
    })

    if not status:
        logger.error(f"Query Analysis LLM 호출 실패: {response}")
        return {"has_error": True, "observation": f"LLM Error: {response}"}

    try:
        cleaned_response = clean_json_string(response or "")
        analyzed_data = json.loads(cleaned_response, strict=False)
        
        plan = analyzed_data.get("step_by_step_plan", "No explicit plan generated. Follow logical steps based on intent.")
        logger.info(f"분석 및 계획 수립 완료: 추출된 키워드 {len(analyzed_data.get('keywords', []))}개")
        logger.info(f"[Plan]: {plan}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 에러. LLM 원본 응답: {response}")
        analyzed_data = {"intent": "Failed to parse", "keywords": [], "skeleton": "", "step_by_step_plan": ""}

    return {
        "analyzed_query": analyzed_data,
        "step_count": state.get("step_count", 0) + 1
    }

def auto_extract_schema(work_dir: str, keywords: list = []) -> str:
    sqlite_files = glob.glob(os.path.join(work_dir, "*.sqlite"))
    if not sqlite_files:
        return "SCHEMA NOT PROVIDED (Database file not found)."
    
    db_path = sqlite_files[0]
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        schema_text = ["[AUTO-EXTRACTED SCHEMA]"]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
        
        if keywords:
            filtered_tables = [t for t in tables if any(k.lower() in t.lower() for k in keywords)]
            tables = filtered_tables if filtered_tables else tables 
        
        for table in tables:
            table_info = f"Table: {table}\nColumns:"
            
            cursor.execute(f"PRAGMA table_info('{table}');")
            columns = cursor.fetchall()
            for col in columns:
                table_info += f"\n  - {col[1]} ({col[2]})"
            
            cursor.execute(f"PRAGMA foreign_key_list('{table}');")
            fks = cursor.fetchall()
            if fks:
                table_info += "\nForeign Keys:"
                for fk in fks:
                    table_info += f"\n  - {fk[3]} references {fk[2]}({fk[4]})"
            
            schema_text.append(table_info)
            
        conn.close()
        return "\n\n".join(schema_text)
        
    except Exception as e:
        logger.error(f"스키마 자동 추출 실패: {e}")
        return f"SCHEMA NOT PROVIDED (Auto-extraction failed: {e})"

def schema_linking_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Schema Linking 실행 중...")
    
    question = state.get("question", "")
    db_id = state.get("db_id", "")
    work_dir = state.get("working_dir", "")
    analysis = state.get("analyzed_query", {})
    
    if not analysis:
        logger.warning("Query Analysis 결과가 없습니다. 기본 질문으로 진행합니다.")
        analysis = {"keywords": [], "intent": question}

    keywords_list = analysis.get("keywords") or []
    keywords_str = ", ".join(keywords_list)
    intent = analysis.get("intent", "")

    logger.info(f"키워드 기반 스키마 필터링 시작 (DB: {db_id})")
    
    filtered_schema = llm_based_schema_linking(
        question=question,
        intent=intent,
        keywords=keywords_str,
        db_id=db_id
    )
    
    schema_str = str(filtered_schema).strip().lower() if filtered_schema else ""
    
    if not schema_str or "error" in schema_str or "not found" in schema_str:
        logger.warning(f"🚨 [Schema Linking] DB({db_id}) 스키마 파일 누락. Python 자동 추출 스크립트 가동!")
        
        extracted_schema = auto_extract_schema(work_dir, keywords_list)
        
        if "SCHEMA NOT PROVIDED" in extracted_schema:
            logger.error("🚨 DB 파일 접근 실패. 최후의 Zero-Shot 탐색 모드로 전환.")
            filtered_schema = "SCHEMA NOT PROVIDED. You MUST use [EXPLORE SQL] with `SELECT name FROM sqlite_master WHERE type='table';` and `PRAGMA table_info()` to discover the database structure yourself."
        else:
            logger.info("✅ Python 스키마 동적 자동 추출 완벽 성공!")
            filtered_schema = extracted_schema
            
    return {
        "retrieved_schema": filtered_schema,
        "step_count": state.get("step_count", 0) + 1
    }
    
def data_profiling_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Data Profiling 실행 중...")
    
    question = state.get("question", "")
    schema = state.get("retrieved_schema", "")
    work_dir = state.get("working_dir", "")
    
    if "SCHEMA NOT PROVIDED" in schema:
        logger.info("⏭️ 스키마가 없으므로 Data Profiling을 건너뜁니다.")
        return {
            "profiled_data": "No profiling executed because schema is unknown. Discover schema first via EXPLORE SQL.",
            "step_count": state.get("step_count", 0) + 1
        }
    
    user_content = f"User Question: {question}\n\nSchema:\n{schema}"
    
    status, response = call_llm({
        "messages": [
            {"role": "system", "content": DATA_PROFILING_SYSTEM},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        "response_mime_type": "application/json"
    })
    
    profiled_data_str = "No profiling data needed or generated."
    
    if status:
        try:
            result_data = json.loads(clean_json_string(response))
            sqls = result_data.get("profiling_sqls", [])
            
            if sqls:
                sqlite_files = glob.glob(os.path.join(work_dir, "*.sqlite"))
                if sqlite_files:
                    db_path = sqlite_files[0]
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    profiling_results = []
                    for sql in sqls[:3]:
                        is_timeout = False
                        def timeout_handler():
                            nonlocal is_timeout
                            is_timeout = True
                            conn.interrupt()
                            
                        timer = threading.Timer(5.0, timeout_handler)
                        
                        try:
                            timer.start()
                            cursor.execute(sql)
                            rows = cursor.fetchall()
                            values = [str(row[0]) for row in rows]
                            profiling_results.append(f"Query: {sql}\nActual Values: {values}")
                        except sqlite3.OperationalError as e:
                            if is_timeout:
                                logger.warning(f"🚨 [Data Profiling] 쿼리 타임아웃(5초 초과): {sql}")
                                profiling_results.append(f"Query: {sql}\nError: Execution Timeout (Over 5 seconds).")
                            else:
                                profiling_results.append(f"Query: {sql}\nError: {str(e)}")
                        except Exception as e:
                            profiling_results.append(f"Query: {sql}\nError: {str(e)}")
                        finally:
                            timer.cancel()
                            
                    conn.close()
                    if profiling_results:
                        profiled_data_str = "\n\n".join(profiling_results)
                    
        except Exception as e:
            logger.warning(f"데이터 프로파일링 파싱/실행 실패: {e}")
            
    logger.info(f"✨ 프로파일링 완료:\n{profiled_data_str}")
    
    return {
        "profiled_data": profiled_data_str,
        "step_count": state.get("step_count", 0) + 1
    }

def load_domain_rules(work_dir: str) -> str:
    """작업 디렉토리 내의 도메인 특화 룰(.txt)을 스캔하여 텍스트로 반환합니다."""
    if not work_dir:
        return ""
    
    txt_files = glob.glob(os.path.join(work_dir, "*.txt"))
    rules = []
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    rules.append(f"--- [Domain Info: {os.path.basename(txt_file)}] ---\n{content}")
        except Exception as e:
            logger.warning(f"도메인 파일 읽기 실패 ({txt_file}): {e}")
            
    return "\n\n".join(rules)
# =====================================================================
# 💡 [개선] Writer 노드: 도메인 룰 로직 제거
# =====================================================================
def sql_writer_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] SQL Writer 실행 중... (최초 작성)")
    
    question = state.get("question", "")
    schema = state.get("retrieved_schema", "")
    profiled = state.get("profiled_data", "No profiling data.")
    plan = state.get("analyzed_query", {}).get("step_by_step_plan", "")
    work_dir = state.get("working_dir", "") # working_dir 가져오기

    persona_prompt = (
        "You are an Expert SQL Architect and Data Analyst (WRITER).\n"
        "Your goal is to write the most efficient and accurate initial SQL query "
        "based on the provided schema, data profiling, and the execution plan.\n"
    )
    
    # 도메인 룰 파일 로드 및 프롬프트 합성
    domain_rules = load_domain_rules(work_dir)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES & HINTS]\n{domain_rules}\n" if domain_rules else ""
    
    dynamic_system_prompt = persona_prompt + domain_prompt + "\n" + SQL_GENERATION_SYSTEM
    
    user_content = (
        f"User Question: {question}\n\n"
        f"Step-by-Step Plan: {plan}\n\n"
        f"Filtered Schema:\n{schema}\n\n"
        "--- DATA PROFILING (Actual Data Values in DB) ---\n"
        f"{profiled}\n\n"
        f"Based on the schema and plan, write your EXPLORE query to test, or the FINAL query to submit."
    )

    messages = [
        {"role": "system", "content": dynamic_system_prompt},
        {"role": "user", "content": user_content}
    ]

    status, response = call_llm({
        "messages": messages,
        "max_tokens": 8192,
        "temperature": 0.0
    })

    try:
        final_sql, is_final = parse_llm_sql_output(response or "")
    except Exception as e:
        logger.error(f"파싱 중 에러 발생: {e}")
        final_sql, is_final = "ERROR", False

    return {
        "generated_code": final_sql,
        "is_final_answer": is_final,
        "has_error": False
    }

# =====================================================================
# 💡 [개선] Modifier 노드: 도메인 룰 로직 제거
# =====================================================================
def sql_modifier_node(state: AgentState) -> Dict[str, Any]:
    retry_count = state.get("retry_count", 0)
    logger.info(f"==> [Node] SQL Modifier 실행 중... (Step: {retry_count+1}/{state.get('max_steps')})")
    
    question = state.get("question", "")
    schema = state.get("retrieved_schema", "")
    history = state.get("execution_history", [])
    profiled = state.get("profiled_data", "No profiling data.")
    plan = state.get("analyzed_query", {}).get("step_by_step_plan", "")
    work_dir = state.get("working_dir", "") # working_dir 가져오기

    persona_prompt = (
        "You are a Senior SQL Debugger and Modifier (MODIFIER).\n"
        "The previous SQL query failed during execution or was rejected by the Logic Critic.\n"
        "DO NOT write a completely new query from scratch. Carefully analyze the [PAST EXECUTION HISTORY] "
        "and the specific [LAST ERROR / FEEDBACK] at the bottom.\n"
        "Identify the exact syntax error, timeout cause, or logical flaw, and provide the corrected SQL.\n"
    )
    
    # 도메인 룰 파일 로드 및 프롬프트 합성
    domain_rules = load_domain_rules(work_dir)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES & HINTS]\n{domain_rules}\n" if domain_rules else ""
    
    dynamic_system_prompt = persona_prompt + domain_prompt + "\n" + SQL_GENERATION_SYSTEM

    recent_history = history 
    history_text = "\n".join([f"Step {i+1} - Executed: {h['sql']}\nResult: {h['result']}" for i, h in enumerate(recent_history)])
    
    user_content = (
        f"User Question: {question}\n\n"
        f"Step-by-Step Plan: {plan}\n\n"
        f"Filtered Schema:\n{schema}\n\n"
        "--- DATA PROFILING (Actual Data Values in DB) ---\n"
        f"{profiled}\n\n"
        f"--- PAST EXECUTION HISTORY ---\n"
        f"{history_text if recent_history else 'No past executions yet.'}\n"
        f"------------------------------\n"
        f"Based on the history and errors, write your next EXPLORE query to debug, or the FINAL query to submit."
    )

    messages = [
        {"role": "system", "content": dynamic_system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    if state.get("has_error") and state.get("observation"):
        obs = state.get("observation", "")
        if "Critic Feedback" in obs or "CRITICAL ERROR" in obs:
            error_header = "🚨 [CRITIC LOGIC REJECTION]"
        elif "Timeout" in obs:
            error_header = "⏳ [DATABASE TIMEOUT ERROR - OPTIMIZE QUERY]"
        else:
            error_header = "❌ [SQL RUNTIME/SYNTAX ERROR]"
            
        messages[1]["content"] += f"\n\n{error_header}\n{obs}\n\nYou MUST fix this specific issue in your next query."

    status, response = call_llm({
        "messages": messages,
        "max_tokens": 8192,
        "temperature": 0.0
    })

    try:
        final_sql, is_final = parse_llm_sql_output(response or "")
    except Exception as e:
        logger.error(f"파싱 중 에러 발생: {e}")
        final_sql, is_final = "ERROR", False

    return {
        "generated_code": final_sql,
        "is_final_answer": is_final,
        "has_error": False
    }

def execution_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Execution 실행 중...")
    
    generated_sql = state.get("generated_code", "")
    logger.info(f"📝 [Generated SQL]:\n{generated_sql}")
    work_dir = state.get("working_dir", "")
    is_final = state.get("is_final_answer", False)
    history = state.get("execution_history", [])
    
    current_sql_strip = generated_sql.strip()

    if current_sql_strip and current_sql_strip != "ERROR":
        same_sql_count = sum(1 for h in history if h.get("sql", "").strip() == current_sql_strip)
        if same_sql_count >= 3:
            logger.error("🚨 [조기 종료] 동일한 오답 쿼리를 3회 이상 제출했습니다. 무한 루프를 강제 차단합니다.")
            return {
                "observation": "Fatal Error: Agent is stuck in an infinite repetition loop.",
                "has_error": True,
                "retry_count": state.get("max_steps", 40)
            }

    past_sqls = [h["sql"].strip().upper() for h in history]
    if generated_sql.strip().upper() in past_sqls:
        logger.warning("🚨 [헛바퀴 방지] 이미 실행했던 SQL입니다. 실행을 차단하고 다른 방법을 유도합니다.")
        error_msg = "ANTI-REPETITION ERROR: You have ALREADY executed this exact query in a previous step. Read your PAST EXECUTION HISTORY to find the result, and DO NOT run this query again. Move on to the next logical step."
        history.append({"sql": generated_sql, "result": error_msg})
        return {
            "execution_history": history,
            "has_error": True,
            "retry_count": state.get("retry_count", 0) + 1,
            "observation": error_msg
        }
    
    if generated_sql == "ERROR" or not generated_sql:
        format_warning = (
            "🚨 SYSTEM FORMAT ERROR 🚨\n"
            "I could not find your SQL query. You MUST strictly use the predefined JSON format or tags.\n"
            "If using raw text, DO NOT use markdown (```sql) without valid JSON structure!"
        )
        logger.warning("🚨 [포맷 에러] 폴백 파서조차 쿼리를 찾지 못했습니다.")
        return {"has_error": True, "observation": format_warning, "retry_count": state.get("retry_count", 0) + 1}
    
    sqlite_files = glob.glob(os.path.join(work_dir, "*.sqlite"))
    if not sqlite_files:
        return {"has_error": True, "observation": "DB file not found.", "retry_count": state.get("retry_count", 0) + 1}
        
    db_path = sqlite_files[0]
    statements = [stmt.strip() for stmt in generated_sql.split(';') if stmt.strip()]

    try:
        for stmt in statements:
            parsed_ast = sqlglot.parse_one(stmt, read="sqlite")
            if not isinstance(parsed_ast, (exp.Select, exp.CTE, exp.Pragma, exp.Create, exp.Drop)):
                raise ValueError(f"Destructive or unsupported query type detected: {type(parsed_ast).__name__}. Only SELECT, PRAGMA, CREATE, and DROP are allowed.")
                
    except sqlglot.errors.ParseError as e:
        error_msg = f"SQL Syntax Error (Caught by sqlglot before DB execution): {str(e)}"
        logger.warning(f"🚨 [사전 구문 에러] {error_msg}")
        history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
        return {
            "execution_history": history,
            "observation": error_msg,
            "has_error": True,
            "retry_count": state.get("retry_count", 0) + 1
        }
    except Exception as e:
        error_msg = f"SQL Safety Error: {str(e)}"
        logger.warning(f"🚨 [사전 안전성 에러] {error_msg}")
        history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
        return {
            "execution_history": history,
            "observation": error_msg,
            "has_error": True,
            "retry_count": state.get("retry_count", 0) + 1
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        is_timeout = False
        def timeout_handler():
            nonlocal is_timeout
            is_timeout = True
            conn.interrupt()

        timer = threading.Timer(10.0, timeout_handler)
        timer.start()

        results = []
        headers = []

        try:
            for i, stmt in enumerate(statements):
                cursor.execute(stmt)
                if stmt.upper().startswith(("SELECT", "WITH", "PRAGMA")):
                    results = cursor.fetchall()
                    headers = [description[0] for description in cursor.description] if cursor.description else []
        finally:
            timer.cancel()
            
        if is_timeout:
            raise sqlite3.OperationalError("interrupted")
        
        if not is_final:
            if "PRAGMA" in generated_sql.upper() or "SQLITE_MASTER" in generated_sql.upper():
                if not results:
                    preview = "TABLE DOES NOT EXIST OR HAS NO COLUMNS."
                else:
                    preview = str(results)
            else:
                preview = str(results[:5])
                
            history.append({"sql": generated_sql, "result": f"Headers: {headers}, Data Preview: {preview}"})
            logger.info("탐색 쿼리 실행 성공. 다음 스텝으로 넘어갑니다.")
            conn.close()
            return {
                "execution_history": history,
                "has_error": True, 
                "retry_count": state.get("retry_count", 0) + 1,
                "observation": "Exploration successful. See history."
            }
            
        if is_final:
            if not results or len(results) == 0:
                error_msg = "Logical Error: The query executed successfully but returned NO data (0 rows). Check your JOIN conditions, DATE formats, or WHERE clauses."
                logger.warning(f"🚨 [논리 에러] 빈 결과 반환. 재시도 유도.")
                history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
                conn.close()
                return {
                    "execution_history": history,
                    "observation": error_msg,
                    "has_error": True,
                    "retry_count": state.get("retry_count", 0) + 1
                }
        
        instance_id = state.get("instance_id", "unknown")
        db_id = state.get("db_id", "unknown")
        run_name = state.get("run_name", "default_run") 
        
        output_base_dir = os.path.join(".", "output", run_name, "csv_results", db_id)
        os.makedirs(output_base_dir, exist_ok=True)
        result_csv_path = os.path.join(output_base_dir, f"{instance_id}.csv")
        
        with open(result_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if headers: writer.writerow(headers)
            if results: writer.writerows(results)
   
        preview = str(results[:5]) if results else "EMPTY RESULT (0 rows)"
        logger.info(f"✨ 최종 정답 쿼리 실행 성공! {result_csv_path} 저장 완료. (결과 존재 여부: {bool(results)})")
        conn.close()
        
        return {
            "has_error": False,
            "observation": "Success",
            "final_result_preview": preview
        }
        
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            error_msg = "Execution Timeout (Over 10 seconds). Your query is highly inefficient. STOP using CROSS JOIN with correlated EXISTS subqueries. Avoid heavy string functions like STRFTIME inside loops. Please optimize your query."
            logger.warning("🚨 [경고] 타임아웃 발생! 너무 무거운 쿼리를 강제 중단합니다.")
        else:
            error_msg = str(e)
            
        history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
        if 'conn' in locals(): conn.close()
            
        return {
            "execution_history": history,
            "observation": error_msg,
            "has_error": True,
            "retry_count": state.get("retry_count", 0) + 1
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"SQL 실행 에러: {error_msg}")
        history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
        if 'conn' in locals(): conn.close()
            
        return {
            "execution_history": history,
            "observation": error_msg,
            "has_error": True,
            "retry_count": state.get("retry_count", 0) + 1
        }

def critic_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Critic (비평가) 실행 중...")
    
    question = state.get("question", "")
    sql = state.get("generated_code", "")
    preview = state.get("final_result_preview", "")
    history = state.get("execution_history", [])
    
    if "EMPTY RESULT" in preview or preview == "[]":
        logger.warning("🚨 [Critic] 결과가 비어있습니다 (0 rows). 논리 에러로 간주하고 재시도 유도.")
        error_msg = "CRITICAL ERROR: The query executed successfully but returned NO data (0 rows). Check your JOIN conditions, DATE formats, or WHERE filters."
        history.append({"sql": sql, "result": error_msg})
        return {
            "has_error": True,
            "is_final_answer": False,
            "observation": error_msg,
            "execution_history": history,
            "retry_count": state.get("retry_count", 0) + 1
        }

    user_content = f"Question: {question}\n\nGenerated SQL:\n{sql}\n\nResult Preview:\n{preview}"
    
    status, response = call_llm({
        "messages": [
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        "response_mime_type": "application/json" 
    })

    try:
        parsed = json.loads(clean_json_string(response))
        is_pass = parsed.get("pass", True)
        feedback = parsed.get("feedback", "")

        if not is_pass:
            logger.warning(f"🚨 [Critic] 반려됨: {feedback}")
            enhanced_feedback = (
                f"CRITIC FEEDBACK: {feedback}\n"
                "🚨 STOP GUESSING. DO NOT write a [FINAL SQL] in your next step. "
                "You MUST write an [EXPLORE SQL] to check the table data, count rows, or verify your JOIN logic first."
            )
            history.append({"sql": sql, "result": enhanced_feedback})
            return {
                "has_error": True,
                "is_final_answer": False,
                "observation": f"Critic Feedback: {feedback}",
                "execution_history": history,
                "retry_count": state.get("retry_count", 0) + 1
            }
        else:
            logger.info("✅ [Critic] 통과! 완벽한 쿼리입니다.")
            return {"has_error": False}
            
    except Exception as e:
        logger.error(f"Critic 파싱 에러 (일단 통과시킴): {e}")
        return {"has_error": False}