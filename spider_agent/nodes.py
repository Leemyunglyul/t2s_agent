import json
import logging
import re
import sqlite3
import os
import glob
import threading
import csv
import math
import yaml
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
    CRITIC_SYSTEM_PROMPT,
    ERROR_GUIDELINES
)

logger = logging.getLogger("langgraph_agent")

def clean_json_string(raw_string: str) -> str:
    match = re.search(r'\{.*\}', raw_string, re.DOTALL)
    if match:
        return match.group(0)
    return raw_string

def parse_llm_sql_output(response_text: str) -> Tuple[str, bool]:
    response_text = response_text.strip()
    
    # <thinking> 태그 추출 로직 추가
    thinking_match = re.search(r"<thinking>\s*(.*?)\s*</thinking>", response_text, re.DOTALL | re.IGNORECASE)
    if thinking_match:
        logger.info(f"🧠 [Self-Verification & Thought]:\n{thinking_match.group(1).strip()}")
    else:
        # 기존 [Thought] 태그 하위 호환
        thought_match = re.search(r"\[Thought\]:\s*(.*?)(?=\[EXPLORE SQL\]:|\[FINAL SQL\]:|$)", response_text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            logger.info(f"[Thought]:\n{thought_match.group(1).strip()}")

    # [FINAL SQL] 추출 (최종 정답)
    if "[FINAL SQL]:" in response_text:
        raw_sql = response_text.split("[FINAL SQL]:", 1)[1].strip()
        sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_sql, re.DOTALL | re.IGNORECASE)
        sql = sql_match.group(1).strip() if sql_match else re.sub(r"^```sql\s*|\s*```$", "", raw_sql, flags=re.IGNORECASE).strip()
        logger.info("✨ [텍스트 태그 파싱 성공] FINAL SQL 추출 완료!")
        return sql, True
        
    # [EXPLORE SQL] 추출 (중간 탐색)
    elif "[EXPLORE SQL]:" in response_text:
        raw_sql = response_text.split("[EXPLORE SQL]:", 1)[1].strip()
        sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_sql, re.DOTALL | re.IGNORECASE)
        sql = sql_match.group(1).strip() if sql_match else re.sub(r"^```sql\s*|\s*```$", "", raw_sql, flags=re.IGNORECASE).strip()
        logger.info("🔍 [텍스트 태그 파싱 성공] EXPLORE SQL 추출 완료!")
        return sql, False
        
    # fallback
    sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip(), True
        
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
        "model": "gemini-2.5-flash",
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
                        truncated_row = tuple(str(val)[:100] + '...' if isinstance(val, str) and len(str(val)) > 100 else val for val in row)
                        table_info += f"Row: {truncated_row}\n"
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
    
    # 2. 💡 [수정] LLM 호출 지연에 대비한 스레딩 및 타임아웃(15초) 적용
    api_result = {"status": False, "response": None}
    
    def run_profiling_llm():
        try:
            status, response = call_llm({
                "model": "gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": DATA_PROFILING_SYSTEM},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.0,
                "response_mime_type": "application/json"
            })
            api_result["status"] = status
            api_result["response"] = response
        except Exception as e:
            logger.error(f"Data Profiling LLM 호출 스레드 내부 에러: {e}")

    llm_thread = threading.Thread(target=run_profiling_llm)
    llm_thread.start()
    
    # 최대 15초 대기
    llm_thread.join(timeout=15.0)
    
    # 타임아웃 발생 시 조기 반환 (무한 대기 방지)
    if llm_thread.is_alive():
        logger.warning("🚨 [Data Profiling] LLM API 응답 타임아웃(15초 초과). 프로파일링을 건너뜁니다.")
        return {
            "profiled_data": "Profiling skipped due to API timeout.",
            "step_count": state.get("step_count", 0) + 1
        }
    
    profiled_data_str = "No profiling data needed or generated."
    
    status = api_result["status"]
    response = api_result["response"]
    
    if status and response:
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
                                logger.warning(f"🚨 [Data Profiling] DB 쿼리 타임아웃(5초 초과): {sql}")
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
    
def load_domain_and_semantic_rules(work_dir: str, instance_id: str, db_id: str) -> str:
    """
    격리된 폴더가 아닌, 실제 룰 파일이 있는 고정 폴더에서 텍스트를 읽어옵니다.
    """
    rules = []
    
    # 1. 시맨틱 모델 탐색 (.yaml)
    if instance_id:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        semantic_path = os.path.join(current_dir, "..", "semantic_models", f"{instance_id}.yaml")
        
        if os.path.exists(semantic_path):
            try:
                with open(semantic_path, 'r', encoding='utf-8') as f:
                    semantic_data = yaml.safe_load(f)
                    if semantic_data:
                        semantic_text = f"--- [SEMANTIC KNOWLEDGE BASE FOR '{instance_id}'] ---\n"
                        semantic_text += yaml.dump(semantic_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
                        rules.append(semantic_text)
                        logger.info(f"🧠 [{instance_id}] 시맨틱 모델(.yaml) 적용 완료!")
            except Exception as e:
                logger.warning(f"시맨틱 모델 읽기 실패: {e}")

    # 2. 도메인 룰 탐색 (.txt) 
    # 🚨 DB ID와 정확히 일치하는 txt 파일 하나만 읽어옵니다.
    if db_id:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 폴더 이름을 'guidelines'로 지정합니다.
        rules_dir = os.path.join(current_dir, "..", "guidelines") 
        
        # db_id와 일치하는 특정 파일의 경로를 만듭니다 (예: guidelines/bank_sales_trading.txt)
        specific_txt_file = os.path.join(rules_dir, f"{db_id}.txt")
        
        if os.path.exists(specific_txt_file):
            try:
                with open(specific_txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        rules.append(f"--- [Domain Info: {os.path.basename(specific_txt_file)}] ---\n{content}")
                        logger.info(f"📜 룰 파일 적용 완료: {os.path.basename(specific_txt_file)}")
            except Exception as e:
                logger.warning(f"도메인 파일 읽기 실패 ({specific_txt_file}): {e}")
                
    return "\n\n".join(rules)

def query_planning_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Query Planning (실행 계획 수립) 실행 중...")
    
    question = state.get("question", "")
    schema = state.get("retrieved_schema", "")
    profiled = state.get("profiled_data", "No profiling data.")
    work_dir = state.get("working_dir", "")
    db_id = state.get("db_id", "")
    
    instance_id = state.get("instance_id", "")
    
    domain_rules = load_domain_and_semantic_rules(work_dir, instance_id, db_id)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES & HINTS]\n{domain_rules}\n" if domain_rules else ""
    
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
        "model": "gemini-2.5-flash",
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
    db_id = state.get("db_id", "")

    instance_id = state.get("instance_id", "")
    
    domain_rules = load_domain_and_semantic_rules(work_dir, instance_id, db_id)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES & HINTS]\n{domain_rules}\n" if domain_rules else ""

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
    work_dir = state.get("working_dir", "")
    obs = state.get("observation", "")

    # 💡 [추가] Observation 분석을 통한 동적 가이드라인 매핑
    selected_guideline = ERROR_GUIDELINES["DEFAULT"]
    if "Syntax Error" in obs or "no such" in obs.lower() or "ambiguous" in obs.lower():
        selected_guideline = ERROR_GUIDELINES["SYNTAX"]
    elif "Critic Feedback" in obs or "REJECTION" in obs:
        selected_guideline = ERROR_GUIDELINES["LOGIC"]
    elif "Timeout" in obs:
        selected_guideline = ERROR_GUIDELINES["TIMEOUT"]
    elif "0 rows" in obs or "Logical Error" in obs:
        selected_guideline = ERROR_GUIDELINES["ZERO_ROWS"]
    elif "SYSTEM FORMAT ERROR" in obs or "파싱 중 에러" in obs:
        selected_guideline = ERROR_GUIDELINES["PARSING"]

    instance_id = state.get("instance_id", "")
    db_id = state.get("db_id", "")

    domain_rules = load_domain_and_semantic_rules(work_dir, instance_id, db_id)
    domain_prompt = f"\n# [DOMAIN SPECIFIC RULES & HINTS]\n{domain_rules}\n" if domain_rules else ""

    # 시스템 프롬프트에 선택된 가이드라인 동적 주입
    dynamic_system_prompt = (
        f"{SQL_MODIFIER_PERSONA}\n\n{SQL_GENERATION_SYSTEM}\n{domain_prompt}\n\n"
        f"# [CRITICAL DEBUGGING GUIDELINE]\n{selected_guideline}"
    )

    history_text = "\n".join([f"Step {i+1} - Executed: {h['sql']}\nResult: {h['result']}" for i, h in enumerate(history)])
    
    user_content = (
        f"User Question: {question}\n\n"
        f"Step-by-Step Plan: {plan}\n\n"
        f"Filtered Schema:\n{schema}\n\n"
        "--- DATA PROFILING (Actual Data Values in DB) ---\n"
        f"{profiled}\n\n"
        f"--- PAST EXECUTION HISTORY ---\n"
        f"{history_text if history else 'No past executions yet.'}\n"
        f"------------------------------\n"
        f"--- LAST ERROR / OBSERVATION ---\n{obs}\n\n"
        f"Based on the history and errors, apply the DEBUGGING GUIDELINE and write your next EXPLORE query to debug, or the FINAL query to submit."
    )
    
    dynamic_temp = min(0.3, retry_count * 0.1)
    if retry_count > 0:
        logger.info(f"🔥 반복 실패 탈출을 위해 Temperature를 {dynamic_temp:.2f}로 상향 조정합니다.")

    messages = [
        {"role": "system", "content": dynamic_system_prompt},
        {"role": "user", "content": user_content}
    ]

    status, response = call_llm({
        "model": "gemini-2.5-pro",
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

    # 1. 무한 루프 1차 방어
    if current_sql_strip and current_sql_strip != "ERROR":
        same_sql_count = sum(1 for h in history if h.get("sql", "").strip() == current_sql_strip)
        if same_sql_count >= 3:
            logger.error("🚨 [조기 종료] 동일한 오답 쿼리를 3회 이상 제출했습니다. 무한 루프를 강제 차단합니다.")
            return {
                "observation": "Fatal Error: Agent is stuck in an infinite repetition loop.",
                "has_error": True,
                "retry_count": state.get("max_steps", 40)
            }

    # 2. 💡 [수정] 무한 루프 2차 방어 (Anti-Repetition 에러 메시지 강화)
    current_sql_upper = generated_sql.strip().upper()
    matching_history = [h for h in history if h.get("sql", "").strip().upper() == current_sql_upper]
    
    if matching_history:
        last_result = matching_history[-1].get("result", "")
        if last_result.startswith("Headers:"):
            logger.info("💡 [헛바퀴 통과] 이전에 성공했던 탐색(EXPLORE) 쿼리를 최종 제출했습니다. 정상 진행합니다.")
        else:
            logger.warning("🚨 [헛바퀴 방지] 이전에 실패/반려된 SQL을 똑같이 제출했습니다. 실행을 차단합니다.")
            # 실패 원인을 명확하게 리턴
            error_msg = f"ANTI-REPETITION ERROR: You already executed this exact query. It previously failed with: [{last_result}]. DO NOT submit it again. You must change your logic."
            history.append({"sql": generated_sql, "result": error_msg})
            return {
                "execution_history": history,
                "has_error": True,
                "retry_count": state.get("retry_count", 0) + 1,
                "observation": error_msg
            }
    
    # 3. 포맷 에러
    if generated_sql == "ERROR" or not generated_sql:
        format_warning = "🚨 SYSTEM FORMAT ERROR 🚨\nI could not find your SQL query. You MUST strictly use the predefined JSON format or tags."
        logger.warning("🚨 [포맷 에러] 쿼리를 찾지 못했습니다.")
        return {"has_error": True, "observation": format_warning, "retry_count": state.get("retry_count", 0) + 1}
    
    # 4. DB 연결 확인
    sqlite_files = glob.glob(os.path.join(work_dir, "*.sqlite"))
    if not sqlite_files:
        return {"has_error": True, "observation": "DB file not found.", "retry_count": state.get("retry_count", 0) + 1}
        
    db_path = sqlite_files[0]
    statements = [stmt.strip() for stmt in generated_sql.split(';') if stmt.strip()]

    # 5. SQLGlot 문법 검사
    try:
        for stmt in statements:
            parsed_ast = sqlglot.parse_one(stmt, read="sqlite")
            if not isinstance(parsed_ast, (exp.Select, exp.CTE, exp.Pragma, exp.Create, exp.Drop)):
                raise ValueError(f"Destructive or unsupported query type detected: {type(parsed_ast).__name__}.")
    except Exception as e:
        error_msg = f"SQL Syntax/Safety Error (Caught before DB execution): {str(e)}"
        logger.warning(f"🚨 [사전 안전성 에러] {error_msg}")
        history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
        return {"execution_history": history, "observation": error_msg, "has_error": True, "retry_count": state.get("retry_count", 0) + 1}

    # 6. 실제 데이터베이스 실행
    try:
        conn = sqlite3.connect(db_path)
        # 수학 함수 주입 생략 (기존과 동일)
        conn.create_function("SQRT", 1, math.sqrt)
        conn.create_function("POWER", 2, math.pow)
        cursor = conn.cursor()
        
        is_timeout = False
        def timeout_handler():
            nonlocal is_timeout
            is_timeout = True
            conn.interrupt()

        timer = threading.Timer(10.0, timeout_handler)
        timer.start()

        results, headers = [], []
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
        
        # 7. EXPLORE 결과 처리
        if not is_final:
            if "PRAGMA" in generated_sql.upper() or "SQLITE_MASTER" in generated_sql.upper():
                preview = "TABLE DOES NOT EXIST OR HAS NO COLUMNS." if not results else str(results)
            else:
                preview = str(results[:5])
                
            history.append({"sql": generated_sql, "result": f"Headers: {headers}, Data Preview: {preview}"})
            logger.info("탐색 쿼리 실행 성공. 다음 스텝으로 넘어갑니다.")
            conn.close()
            return {"execution_history": history, "has_error": True, "retry_count": state.get("retry_count", 0) + 1, "observation": "Exploration successful. See history."}
            
        # 8. 💡 [수정] FINAL 쿼리 0 rows 에러 처리 강화
        if is_final:
            if not results or len(results) == 0:
                error_msg = (
                    "Logical Error: The query executed successfully but returned NO data (0 rows). "
                    "This indicates over-filtering or mismatched JOIN conditions. "
                    "ACTION: Use [EXPLORE SQL] to run 'SELECT col_name, COUNT(*) FROM table GROUP BY 1 LIMIT 20' to verify actual data values."
                )
                logger.warning("🚨 [논리 에러] 빈 결과 반환. 재시도 유도.")
                history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
                conn.close()
                return {"execution_history": history, "observation": error_msg, "has_error": True, "retry_count": state.get("retry_count", 0) + 1}
        
        # CSV 저장
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
        logger.info(f"✨ 최종 정답 쿼리 실행 성공! {result_csv_path} 저장 완료.")
        conn.close()
        
        return {"has_error": False, "observation": "Success", "final_result_preview": preview}
        
    except Exception as e:
        error_msg = str(e)
        if "interrupted" in error_msg.lower():
            error_msg = "Execution Timeout (Over 10 seconds). Query is too inefficient."
        
        logger.warning(f"SQL 실행 에러: {error_msg}")
        history.append({"sql": generated_sql, "result": f"ERROR: {error_msg}"})
        if 'conn' in locals(): conn.close()
        return {"execution_history": history, "observation": error_msg, "has_error": True, "retry_count": state.get("retry_count", 0) + 1}

def critic_node(state: AgentState) -> Dict[str, Any]:
    logger.info("==> [Node] Critic (비평가) 실행 중...")
    
    question = state.get("question", "")
    sql = state.get("generated_code", "")
    preview = state.get("final_result_preview", "")
    history = state.get("execution_history", [])
    work_dir = state.get("working_dir", "")
    db_id = state.get("db_id", "")    
    instance_id = state.get("instance_id", "")
    
    domain_rules = load_domain_and_semantic_rules(work_dir, instance_id, db_id)
    domain_prompt = f"\n# [STRICT BENCHMARK RULES]\nYou MUST check if the Generated SQL strictly follows these rules:\n{domain_rules}\n" if domain_rules else ""
    
    user_content = f"Question: {question}\n\nGenerated SQL:\n{sql}\n\nResult Preview:\n{preview}\n{domain_prompt}"
    
    status, response = call_llm({
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        "response_mime_type": "application/json" 
    })

    # 💡 [수정] Critic Fail-Safe 로직 완벽 적용
    if not status or not response:
        logger.error("🚨 Critic API 호출 실패 또는 빈 응답")
        return {
            "has_error": True, 
            "observation": ERROR_GUIDELINES["PARSING"],
            "retry_count": state.get("retry_count", 0) + 1
        }

    try:
        parsed = json.loads(clean_json_string(response))
        is_pass = parsed.get("pass", True)
        feedback = parsed.get("feedback", "")
        violated_rule = parsed.get("violated_rule", "N/A") # 어떤 체크리스트를 위반했는지 확인

        if not is_pass:
            logger.warning(f"🚨 [Critic] 반려됨: {feedback} (Rule: {violated_rule})")
            enhanced_feedback = (
                f"🚨 [CRITIC REJECTION]\n"
                f"Violated Rule: {violated_rule}\n"
                f"Feedback: {feedback}\n"
                "ACTION: DO NOT write a [FINAL SQL] immediately. Write an [EXPLORE SQL] to verify your new logic first."
            )
            history.append({"sql": sql, "result": enhanced_feedback})
            return {
                "has_error": True,
                "is_final_answer": False,
                "observation": enhanced_feedback,
                "execution_history": history,
                "retry_count": state.get("retry_count", 0) + 1
            }
        else:
            logger.info("✅ [Critic] 통과! 완벽한 쿼리입니다.")
            return {"has_error": False}
            
    except Exception as e:
        # 무조건 통과시키지 않고 에러 반환 및 재시도 유도
        logger.error(f"Critic 파싱 에러: {e}")
        return {
            "has_error": True, 
            "observation": ERROR_GUIDELINES["PARSING"],
            "retry_count": state.get("retry_count", 0) + 1
        }