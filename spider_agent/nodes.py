import json
import logging
import re
import sqlite3
import os
import glob
import threading
import csv
import math
from typing import Dict, Any, Tuple

import sqlglot
from sqlglot import exp

from .llm import call_llm
from .state import AgentState
from .prompts import (
    KEYWORD_EXTRACTION_SYSTEM, 
    QUERY_PLANNING_SYSTEM, 
    SCHEMA_LINKING_SYSTEM, 
    SQL_GENERATION_SYSTEM,
    SQL_MODIFIER_PERSONA,
    SQL_WRITER_PERSONA, 
    DATA_PROFILING_SYSTEM, 
    CRITIC_SYSTEM_PROMPT
)
from .tools import llm_based_schema_linking

logger = logging.getLogger("langgraph_agent")

def clean_json_string(raw_string: str) -> str:
    match = re.search(r'\{.*\}', raw_string, re.DOTALL)
    if match:
        return match.group(0)
    return raw_string

def parse_llm_sql_output(response_text: str) -> Tuple[str, bool]:
    response_text = response_text.strip()
    
    # 1. JSON 포맷 파싱 시도 (우선순위)
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

    # 2. 텍스트 태그 포맷 파싱 (JSON 파싱 실패 시 차선책)
    # [Thought] 내용 추출
    thought_match = re.search(r"\[Thought\]:\s*(.*?)(?=\[EXPLORE SQL\]:|\[FINAL SQL\]:|$)", response_text, re.DOTALL | re.IGNORECASE)
    if thought_match:
        logger.info(f"[Thought]:\n{thought_match.group(1).strip()}")

    # [FINAL SQL] 추출 (최종 정답)
    if "[FINAL SQL]:" in response_text:
        raw_sql = response_text.split("[FINAL SQL]:", 1)[1].strip()
        sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_sql, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            sql = re.sub(r"^```sql\s*|\s*```$", "", raw_sql, flags=re.IGNORECASE).strip()
            
        logger.info("✨ [텍스트 태그 파싱 성공] FINAL SQL 추출 완료!")
        return sql, True
        
    # [EXPLORE SQL] 추출 (중간 탐색)
    elif "[EXPLORE SQL]:" in response_text:
        raw_sql = response_text.split("[EXPLORE SQL]:", 1)[1].strip()
        sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_sql, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            sql = re.sub(r"^```sql\s*|\s*```$", "", raw_sql, flags=re.IGNORECASE).strip()
            
        logger.info("🔍 [텍스트 태그 파싱 성공] EXPLORE SQL 추출 완료!")
        return sql, False
        
    # 3. 태그 누락 시 최후의 보루 (마크다운 블록 또는 SQL 예약어로 강제 추출)
    logger.warning("🚨 태그 형식 누락! 정규식 강제 추출 시도.")
    sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip(), True
    elif response_text.upper().startswith(("SELECT", "WITH", "CREATE", "DROP", "PRAGMA")):
        return response_text, True
        
    return response_text, True

def keyword_extraction_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Keyword Extraction 실행 중...")
    
    question = state.get("question", "")
    if not question:
        logger.error("State에 'question'이 없습니다.")
        return {"has_error": True, "observation": "Missing question in state."}

    messages = [
        {"role": "system", "content": KEYWORD_EXTRACTION_SYSTEM},
        {"role": "user", "content": f"User Question: \"{question}\""}
    ]
    
    status, response = call_llm({
        "model": "gemini-2.5-flash-lite",
        "messages": messages,
        "temperature": 0.0,
        "response_mime_type": "application/json"
    })

    if not status:
        logger.error(f"Keyword Extraction LLM 호출 실패: {response}")
        return {"has_error": True, "observation": f"LLM Error: {response}"}

    try:
        cleaned_response = clean_json_string(response or "")
        analyzed_data = json.loads(cleaned_response, strict=False)
        logger.info(f"키워드 추출 완료: {len(analyzed_data.get('keywords', []))}개")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 에러. LLM 원본 응답: {response}")
        analyzed_data = {"intent": "Failed to parse", "keywords": [], "skeleton": ""}

    return {
        "analyzed_query": analyzed_data,
        "step_count": state.get("step_count", 0) + 1
    }

def extractive_schema_linking(work_dir: str, question: str, keywords: list) -> str:
    sqlite_files = glob.glob(os.path.join(work_dir, "*.sqlite"))
    if not sqlite_files:
        return "SCHEMA NOT PROVIDED (Database file not found)."
    
    db_path = sqlite_files[0]
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. DB 전체의 가벼운 구조(테이블 및 컬럼명만) 추출
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        tables = [row[0] for row in cursor.fetchall()]
        
        lightweight_schema = []
        for t in tables:
            cursor.execute(f"PRAGMA table_info('{t}')")
            cols = [row[1] for row in cursor.fetchall()]
            lightweight_schema.append(f"Table: {t} | Columns: {', '.join(cols)}")
            
        lightweight_schema_str = "\n".join(lightweight_schema)
        
        # 2. IBM 논문 기반: Fine-grained Schema Linker 프롬프트 작성
        sl_prompt = f"""
        You are an Extractive Schema Linker for Text-to-SQL.
        Your task is to identify which tables and columns are relevant to the user's question, and define their roles.
        PRIORITIZE RECALL: It is extremely important not to miss JOIN keys (Foreign/Primary keys). If unsure, include them.

        Roles:
        - selected: Columns used in the SELECT clause.
        - join: Columns used to JOIN tables (CRITICAL: Find overlapping ID columns).
        - condition: Columns used in WHERE or HAVING clauses.
        - group: Columns used in GROUP BY.
        - order: Columns used in ORDER BY.

        User Question: "{question}"
        Target Keywords: {", ".join(keywords)}

        Available Lightweight Schema:
        {lightweight_schema_str}

        Output ONLY a JSON object in this exact format:
        {{
            "relevant_tables": ["table1", "table2"],
            "roles": {{
                "selected": ["table1.colA", "table2.colB"],
                "join": ["table1.id", "table2.table1_id"],
                "condition": ["table2.colC"],
                "group": ["None"],
                "order": ["None"]
            }}
        }}
        """
        
        # 💡 [추가] API 호출 지연에 대비한 상태 변수 및 타임아웃 설정
        selected_tables = tables # 타임아웃 나면 전체 테이블을 쓰기 위한 기본값
        fine_grained_roles = ""
        api_result = {"status": False, "response": None}
        
        # 별도 쓰레드에서 LLM 호출 실행
        def run_llm():
            try:
                status, response = call_llm({
                    "model": "gemini-2.5-flash",
                    "messages": [{"role": "user", "content": sl_prompt}],
                    "temperature": 0.0,
                    "response_mime_type": "application/json"
                })
                api_result["status"] = status
                api_result["response"] = response
            except Exception as e:
                logger.error(f"Schema Linking LLM 호출 스레드 내부 에러: {e}")

        llm_thread = threading.Thread(target=run_llm)
        llm_thread.start()
        
        # 최대 20초까지만 대기 (20초 넘어가면 타임아웃으로 간주하고 전체 테이블 스키마 반환)
        llm_thread.join(timeout=20.0) 
        
        if llm_thread.is_alive():
            logger.warning("🚨 [Schema Linking] LLM API 응답 타임아웃(20초 초과). Fallback: 전체 테이블 사용.")
            # 스레드는 뒷단에서 돌게 냅두고 메인 흐름은 그냥 진행함
        else:
            if api_result["status"] and api_result["response"]:
                try:
                    parsed_sl = json.loads(clean_json_string(api_result["response"]))
                    llm_tables = parsed_sl.get("relevant_tables", [])
                    
                    # 유효한 테이블만 선별
                    valid_tables = [t for t in llm_tables if t in tables]
                    if valid_tables:
                        selected_tables = valid_tables
                        logger.info(f"🧠 [논문 방식: ExSL] 필요 테이블 선별 완료: {selected_tables}")
                    
                    # 논문의 Figure 4 형태(Role 지정)로 문자열 파싱
                    roles = parsed_sl.get("roles", {})
                    fine_grained_roles = "[FINE-GRAINED SCHEMA LINKS (IBM ExSL_f)]\n"
                    for role, cols in roles.items():
                        fine_grained_roles += f"{role}: {', '.join(cols)}\n"
                        
                except Exception as e:
                    logger.warning(f"Extractive Schema Linking 파싱 실패, 전체 테이블 폴백: {e}")

        # 3. 선택된 테이블에 대해서만 Full DDL 및 샘플 데이터(3 rows) 추출
        # (DB 연결을 여기서 다시 맺어주는 것이 스레드 안전성 측면에서 좋습니다)
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        all_tables_data = cursor.fetchall()
        
        schema_text = ["[FOCUSED SCHEMA DDL & SAMPLE DATA]"]
        
        for table_name in selected_tables:
            ddl = next((row[1] for row in all_tables_data if row[0] == table_name), None)
            if not ddl: continue
            
            table_info = f"--- Table: {table_name} ---\n[DDL]\n{ddl}\n"
            
            # 샘플 데이터 3줄 추가
            try:
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 3;")
                rows = cursor.fetchall()
                if rows:
                    col_names = [description[0] for description in cursor.description]
                    table_info += f"[Sample Data (3 rows)]\nColumns: {', '.join(col_names)}\n"
                    for row in rows:
                        table_info += f"Row: {row}\n"
                else:
                    table_info += "[Sample Data]: Table is empty.\n"
            except Exception as e:
                table_info += f"[Sample Data Error]: {e}\n"
                
            schema_text.append(table_info)
            
        conn.close()
        
        # 4. 최종 스키마 조립
        final_schema = "\n\n".join(schema_text)
        if fine_grained_roles:
            final_schema += f"\n\n{fine_grained_roles}"
            
        return final_schema
        
    except Exception as e:
        logger.error(f"스키마 동적 추출 실패: {e}")
        return f"SCHEMA NOT PROVIDED (Extraction failed: {e})"

def schema_linking_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Schema Linking (IBM ExSL) 실행 중...")
    
    question = state.get("question", "")
    db_id = state.get("db_id", "")
    work_dir = state.get("working_dir", "")
    analysis = state.get("analyzed_query", {})
    
    keywords_list = analysis.get("keywords") or []

    # 🌟 수동 YAML 파일 로직을 완전히 제거하고 오직 동적 스키마 추출만 사용합니다.
    logger.info(f"DB({db_id}) 구조 실시간 동적 분석 시작...")
    extracted_schema = extractive_schema_linking(work_dir, question, keywords_list)
    
    if "SCHEMA NOT PROVIDED" in extracted_schema:
        logger.error("🚨 DB 파일 접근 실패. 최후의 Zero-Shot 탐색 모드로 전환.")
        filtered_schema = "SCHEMA NOT PROVIDED. You MUST use [EXPLORE SQL] with `SELECT name FROM sqlite_master WHERE type='table';` and `PRAGMA table_info()` to discover the database structure yourself."
    else:
        logger.info("✅ 논문 기반 동적 스키마(ExSL_f) 추출 완벽 성공!")
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
    
    # 1. 조기 종료: 앞선 노드에서 스키마를 아예 찾지 못했다면 프로파일링 불가능하므로 패스
    if "SCHEMA NOT PROVIDED" in schema:
        logger.info("⏭️ 스키마가 없으므로 Data Profiling을 건너뜁니다.")
        return {
            "profiled_data": "No profiling executed because schema is unknown. Discover schema first via EXPLORE SQL.",
            "step_count": state.get("step_count", 0) + 1
        }
    
    user_content = f"User Question: {question}\n\nSchema:\n{schema}"
    
    # 2. LLM 호출: "질문과 스키마를 볼 때, 데이터 형식을 파악하려면 어떤 쿼리로 찍어봐야 할까?"
    status, response = call_llm({
        "model": "gemini-2.5-flash-lite",
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
            # 3. LLM이 제안한 프로파일링 쿼리(SQL) 목록 추출
            result_data = json.loads(clean_json_string(response))
            sqls = result_data.get("profiling_sqls", [])
            
            if sqls:
                sqlite_files = glob.glob(os.path.join(work_dir, "*.sqlite"))
                if sqlite_files:
                    db_path = sqlite_files[0]
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    profiling_results = []
                    # 토큰 낭비와 시간 지연을 막기 위해 최대 3개의 쿼리만 실행
                    for sql in sqls[:3]:
                        is_timeout = False
                        
                        # 4. 안전장치 (Timeout): 무거운 쿼리가 파이프라인을 뻗게 하는 것을 방지
                        def timeout_handler():
                            nonlocal is_timeout
                            is_timeout = True
                            conn.interrupt() # 5초가 지나면 쿼리 강제 중단
                            
                        timer = threading.Timer(5.0, timeout_handler)
                        
                        try:
                            timer.start()
                            # 5. 쿼리 실행 및 결과값 5개 추출
                            cursor.execute(sql)
                            rows = cursor.fetchall()
                            values = [str(row[0]) for row in rows]
                            profiling_results.append(f"Query: {sql}\nActual Values: {values}")
                            
                        except sqlite3.OperationalError as e:
                            # 타임아웃에 걸려 강제 중단된 경우의 에러 처리
                            if is_timeout:
                                logger.warning(f"🚨 [Data Profiling] 쿼리 타임아웃(5초 초과): {sql}")
                                profiling_results.append(f"Query: {sql}\nError: Execution Timeout (Over 5 seconds).")
                            else:
                                profiling_results.append(f"Query: {sql}\nError: {str(e)}")
                        except Exception as e:
                            profiling_results.append(f"Query: {sql}\nError: {str(e)}")
                        finally:
                            timer.cancel() # 무사히 실행이 끝나면 타이머 해제
                            
                    conn.close()
                    
                    # 6. 추출된 실제 데이터 샘플들을 하나의 문자열로 취합
                    if profiling_results:
                        profiled_data_str = "\n\n".join(profiling_results)
                    
        except Exception as e:
            logger.warning(f"데이터 프로파일링 파싱/실행 실패: {e}")
            
    logger.info(f"✨ 프로파일링 완료:\n{profiled_data_str}")
    
    # 이 노드의 결과(실제 데이터 값들)는 다음 노드(Query Planning/SQL Writer)의 참고 자료로 쓰임
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

def query_planning_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Query Planning (실행 계획 수립) 실행 중...")
    
    question = state.get("question", "")
    schema = state.get("retrieved_schema", "")
    profiled = state.get("profiled_data", "No profiling data.")
    work_dir = state.get("working_dir", "")
    
    domain_rules = load_domain_rules(work_dir)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES]\n{domain_rules}\n" if domain_rules else ""
    
    dynamic_planner_system = QUERY_PLANNING_SYSTEM + domain_prompt
    
    user_content = (
        f"User Question: {question}\n\n"
        f"Filtered Schema:\n{schema}\n\n"
        "--- DATA PROFILING (Actual Data Values in DB) ---\n"
        f"{profiled}\n"
    )
    
    messages = [
        {"role": "system", "content": dynamic_planner_system},
        {"role": "user", "content": user_content}
    ]
    
    status, response = call_llm({
        "model": "gemini-2.5-pro",
        "messages": messages,
        "temperature": 0.0,
        "response_mime_type": "application/json"
    })

    analyzed_query = state.get("analyzed_query", {})
    if status:
        try:
            cleaned_response = clean_json_string(response or "")
            plan_data = json.loads(cleaned_response, strict=False)
            plan = plan_data.get("step_by_step_plan", "No explicit plan generated.")
            analyzed_query["step_by_step_plan"] = plan
            logger.info(f"[Plan]:\n{plan}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 에러. LLM 원본 응답: {response}")
            analyzed_query["step_by_step_plan"] = "Error parsing plan."
            
    return {
        "analyzed_query": analyzed_query,
        "step_count": state.get("step_count", 0) + 1
    }

def sql_writer_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] SQL Writer 실행 중... (최초 작성)")
    
    question = state.get("question", "")
    schema = state.get("retrieved_schema", "")
    profiled = state.get("profiled_data", "No profiling data.")
    plan = state.get("analyzed_query", {}).get("step_by_step_plan", "")
    work_dir = state.get("working_dir", "")

    domain_rules = load_domain_rules(work_dir)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES & HINTS]\n{domain_rules}\n" if domain_rules else ""

    # 💡 시스템 프롬프트에 도메인 룰 합체!
    dynamic_system_prompt = f"{SQL_WRITER_PERSONA}\n\n{SQL_GENERATION_SYSTEM}\n{domain_prompt}"
    
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
        "model": "gemini-2.5-flash",
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


def sql_modifier_node(state: AgentState) -> Dict[str, Any]:
    retry_count = state.get("retry_count", 0)
    logger.info(f"==> [Node] SQL Modifier 실행 중... (Step: {retry_count+1}/{state.get('max_steps')})")
    
    question = state.get("question", "")
    schema = state.get("retrieved_schema", "")
    history = state.get("execution_history", [])
    profiled = state.get("profiled_data", "No profiling data.")
    plan = state.get("analyzed_query", {}).get("step_by_step_plan", "")

    work_dir = state.get("working_dir", "") # 💡 추가: work_dir 가져오기

    domain_rules = load_domain_rules(work_dir)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES & HINTS]\n{domain_rules}\n" if domain_rules else ""

    dynamic_system_prompt = f"{SQL_MODIFIER_PERSONA}\n\n{SQL_GENERATION_SYSTEM}\n{domain_prompt}"

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
    
    dynamic_temp = min(0.3, retry_count * 0.1)
    if retry_count > 0:
        logger.info(f"🔥 반복 실패 탈출을 위해 Temperature를 {dynamic_temp:.2f}로 상향 조정합니다.")

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
        "model": "gemini-2.5-flash",
        "messages": messages,
        "temperature": dynamic_temp
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

    # 1. [안전장치] 무한 루프 1차 방어 (완전히 똑같은 오답을 3번 이상 내면 강제 종료)
    if current_sql_strip and current_sql_strip != "ERROR":
        same_sql_count = sum(1 for h in history if h.get("sql", "").strip() == current_sql_strip)
        if same_sql_count >= 3:
            logger.error("🚨 [조기 종료] 동일한 오답 쿼리를 3회 이상 제출했습니다. 무한 루프를 강제 차단합니다.")
            return {
                "observation": "Fatal Error: Agent is stuck in an infinite repetition loop.",
                "has_error": True,
                "retry_count": state.get("max_steps", 40) # Max Step으로 올려서 그래프를 끝내버림
            }

    # 2. [안전장치] 무한 루프 2차 방어 (직전에 실패했던 쿼리를 토씨 하나 안 틀리고 또 내면 반려)
    current_sql_upper = generated_sql.strip().upper()
    matching_history = [h for h in history if h.get("sql", "").strip().upper() == current_sql_upper]
    
    if matching_history:
        last_result = matching_history[-1].get("result", "")
        
        # 단, 직전에 성공했던 EXPLORE 쿼리를 FINAL로 제출하는 경우는 허용
        if last_result.startswith("Headers:"):
            logger.info("💡 [헛바퀴 통과] 이전에 성공했던 탐색(EXPLORE) 쿼리를 최종 제출했습니다. 정상 진행합니다.")
            pass 
        else:
            logger.warning("🚨 [헛바퀴 방지] 이전에 실패/반려된 SQL을 똑같이 제출했습니다. 실행을 차단합니다.")
            error_msg = "ANTI-REPETITION ERROR: You have ALREADY executed this exact query, and it FAILED or was REJECTED by the Critic. Do NOT submit it again without changes. Fix the logic."
            history.append({"sql": generated_sql, "result": error_msg})
            return {
                "execution_history": history,
                "has_error": True,
                "retry_count": state.get("retry_count", 0) + 1,
                "observation": error_msg
            }
    
    # 3. [안전장치] 포맷 에러 (SQL을 아예 못 뽑아냈을 때)
    if generated_sql == "ERROR" or not generated_sql:
        format_warning = (
            "🚨 SYSTEM FORMAT ERROR 🚨\n"
            "I could not find your SQL query. You MUST strictly use the predefined JSON format or tags.\n"
            "If using raw text, DO NOT use markdown (```sql) without valid JSON structure!"
        )
        logger.warning("🚨 [포맷 에러] 폴백 파서조차 쿼리를 찾지 못했습니다.")
        return {"has_error": True, "observation": format_warning, "retry_count": state.get("retry_count", 0) + 1}
    
    # 4. DB 연결 확인
    sqlite_files = glob.glob(os.path.join(work_dir, "*.sqlite"))
    if not sqlite_files:
        return {"has_error": True, "observation": "DB file not found.", "retry_count": state.get("retry_count", 0) + 1}
        
    db_path = sqlite_files[0]
    statements = [stmt.strip() for stmt in generated_sql.split(';') if stmt.strip()]

    # 5. [안전장치] SQLGlot을 이용한 DDL(DROP, UPDATE 등) 파괴적 쿼리 사전 차단 및 문법 검사
    try:
        for stmt in statements:
            parsed_ast = sqlglot.parse_one(stmt, read="sqlite")
            if not isinstance(parsed_ast, (exp.Select, exp.CTE, exp.Pragma, exp.Create, exp.Drop)):
                raise ValueError(f"Destructive or unsupported query type detected: {type(parsed_ast).__name__}. Only SELECT, PRAGMA, CREATE, and DROP are allowed.")
                
    except sqlglot.errors.ParseError as e:
        # 💡 [추가] 구문 에러 맞춤형 피드백
        error_msg = (
            f"SQL Syntax Error (Caught by sqlglot before DB execution): {str(e)}\n"
            "👉 HOW TO FIX: Check for missing commas, unclosed parentheses, misspelled SQL keywords, or unsupported SQLite syntax. "
            "Ensure CTEs are defined correctly with 'WITH' only once at the very top."
        )
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

    # 6. 실제 데이터베이스 실행 (수학 함수 주입 및 타임아웃 10초 설정)
    try:
        conn = sqlite3.connect(db_path)
        conn.create_function("SQRT", 1, math.sqrt)
        conn.create_function("POWER", 2, math.pow)
        conn.create_function("SIN", 1, math.sin)
        conn.create_function("COS", 1, math.cos)
        conn.create_function("ASIN", 1, math.asin)
        conn.create_function("ACOS", 1, math.acos)
        conn.create_function("ATAN", 1, math.atan)
        conn.create_function("ATAN2", 2, math.atan2)
        conn.create_function("RADIANS", 1, math.radians)
        conn.create_function("PI", 0, lambda: math.pi)
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
        
        # 7. [결과 처리] EXPLORE(탐색) 쿼리인 경우 데이터 일부만 반환하고 다음 스텝 유도
        if not is_final:
            if "PRAGMA" in generated_sql.upper() or "SQLITE_MASTER" in generated_sql.upper():
                if not results:
                    preview = "TABLE DOES NOT EXIST OR HAS NO COLUMNS."
                else:
                    preview = str(results)
            else:
                preview = str(results[:5]) # 데이터를 5줄만 보여줌
                
            history.append({"sql": generated_sql, "result": f"Headers: {headers}, Data Preview: {preview}"})
            logger.info("탐색 쿼리 실행 성공. 다음 스텝으로 넘어갑니다.")
            conn.close()
            return {
                "execution_history": history,
                "has_error": True, # 에러는 아니지만 파이프라인을 계속 돌리기 위해 True 리턴
                "retry_count": state.get("retry_count", 0) + 1,
                "observation": "Exploration successful. See history."
            }
            
        # 8. [결과 처리] FINAL(최종) 쿼리인 경우 로직 에러(0 rows) 검사 후 CSV 저장
        if is_final:
            if not results or len(results) == 0:
                # 💡 [추가] 0 Rows 논리 에러 맞춤형 피드백 (패닉 방지)
                error_msg = (
                    "Logical Error: The query executed successfully but returned NO data (0 rows).\n"
                    "👉 HOW TO FIX: \n"
                    "  1) Your JOIN ON conditions might be mismatched (e.g., comparing 'YYYY-MM-DD' with 'DD-MM-YYYY').\n"
                    "  2) Your WHERE filters might be too strict. \n"
                    "  3) DO NOT PANIC and do not invent dummy data. \n"
                    "  ACTION: Write an [EXPLORE SQL] removing WHERE clauses one by one, or change INNER JOINs to LEFT JOINs to see where the data drops."
                )
                logger.warning(f"🚨 [논리 에러] 빈 결과 반환. 재시도 유도.")
                history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
                conn.close()
                return {
                    "execution_history": history,
                    "observation": error_msg,
                    "has_error": True,
                    "retry_count": state.get("retry_count", 0) + 1
                }
        
        # CSV 파일 저장 로직
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
        
    # 9. [에러 처리] DB 실행 중 타임아웃 또는 일반 에러 발생 시 처리
    except sqlite3.OperationalError as e:
        raw_error = str(e).lower()
        if "interrupted" in raw_error:
            # 💡 [추가] 타임아웃 에러 맞춤형 피드백
            error_msg = (
                "Execution Timeout (Over 10 seconds).\n"
                "👉 HOW TO FIX: Your query is highly inefficient. STOP using CROSS JOIN with correlated EXISTS subqueries. "
                "Avoid heavy string functions like STRFTIME inside ON clauses. You MUST physically aggregate data in a CTE before joining massive tables."
            )
            logger.warning("🚨 [경고] 타임아웃 발생! 너무 무거운 쿼리를 강제 중단합니다.")
        else:
            # 💡 [추가] 일반 DB 실행 에러 (컬럼/테이블 누락 등) 맞춤형 피드백
            hint = ""
            if "no such column" in raw_error:
                hint = "\n👉 HOW TO FIX: You hallucinated a column that does not exist. Check the Filtered Schema. Did you forget a table alias (e.g., 't.column_name')?"
            elif "no such table" in raw_error:
                hint = "\n👉 HOW TO FIX: You queried a table that does not exist. Check the Filtered Schema for the exact table name."
            elif "ambiguous column" in raw_error:
                hint = "\n👉 HOW TO FIX: Two joined tables have the same column name. You MUST explicitly use table aliases (e.g., 'table_a.id = table_b.id')."
            elif "no such function" in raw_error:
                hint = "\n👉 HOW TO FIX: You used a function not supported by SQLite. Use SQLite equivalents."
            
            error_msg = f"Database Execution Error: {str(e)}{hint}"
            
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
    
    # 2. LLM 비평가에게 보낼 데이터 조립 (질문 + 작성된 SQL + 결과 미리보기)
    user_content = f"Question: {question}\n\nGenerated SQL:\n{sql}\n\nResult Preview:\n{preview}"
    
    # 3. 고지능 모델(Pro)을 사용하여 쿼리 논리 검증 수행 (JSON 응답 강제)
    status, response = call_llm({
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        "response_mime_type": "application/json" 
    })

    try:
        # 4. 비평 결과 파싱 (pass 여부와 피드백 내용 추출)
        parsed = json.loads(clean_json_string(response))
        is_pass = parsed.get("pass", True)
        feedback = parsed.get("feedback", "")

        if not is_pass:
            # 5. [반려 시] 에이전트가 찍기(Guessing)를 못하도록 다음 스텝에 데이터 탐색(EXPLORE)을 강제함
            logger.warning(f"🚨 [Critic] 반려됨: {feedback}")
            enhanced_feedback = (
                f"CRITIC FEEDBACK: {feedback}\n"
                "🚨 STOP GUESSING. DO NOT write a [FINAL SQL] in your next step. "
                "You MUST write an [EXPLORE SQL] to check the table data, count rows, or verify your JOIN logic first."
            )
            history.append({"sql": sql, "result": enhanced_feedback})
            return {
                "has_error": True,
                "is_final_answer": False,  # 다시 쿼리를 짜야 하므로 False로 강등
                "observation": f"Critic Feedback: {feedback}",
                "execution_history": history,
                "retry_count": state.get("retry_count", 0) + 1
            }
        else:
            # 6. [통과 시] 완벽한 정답으로 간주하고 파이프라인 종료 유도
            logger.info("✅ [Critic] 통과! 완벽한 쿼리입니다.")
            return {"has_error": False}
            
    except Exception as e:
        # 7. [안전장치] 만약 LLM 응답이 JSON으로 안 떨어져서 파싱 에러가 나면, 
        # 비평가 때문에 전체 프로세스가 뻗는 것을 막기 위해 일단 통과시킴
        logger.error(f"Critic 파싱 에러 (일단 통과시킴): {e}")
        return {"has_error": False}