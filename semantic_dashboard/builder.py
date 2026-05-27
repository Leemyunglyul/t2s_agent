import json
import yaml
import os
import glob
import sys
import sqlite3
import re
import sqlparse
from datetime import datetime
from json_repair import repair_json # 강력한 JSON 복구 라이브러리

# ==========================================
# 💡 1. YAML 저장 시 긴 문자열을 여러 줄(|)로 예쁘게 저장하도록 Dumper 설정
# ==========================================
def multiline_presenter(dumper, data):
    if '\n' in data or len(data) > 60:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, multiline_presenter)

current_dir = os.path.dirname(os.path.abspath(__file__))

parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

target_path = os.path.abspath(os.path.join(current_dir, '..', 'spider_agent'))
sys.path.append(target_path)

# TODO: 실제 환경에 맞게 임포트 경로 확인
from llm import call_llm

GOLDSQL_PATH = os.path.abspath(os.path.join(current_dir, "..", "gold_sql.jsonl"))
SEMANTIC_DIR = os.path.join(current_dir, "semantic_models")
STATE_FILE = os.path.join(current_dir, "latest_intent_state.json")

os.makedirs(SEMANTIC_DIR, exist_ok=True)

# ==========================================
# 💡 2. SQL을 짧고 예쁘게 포매팅하는 함수
# ==========================================
def format_sql(sql_query):
    if not sql_query: return ""
    return sqlparse.format(sql_query, reindent=True, keyword_case='upper', wrap_after=80)

def load_gold_sqls():
    records = []
    if not os.path.exists(GOLDSQL_PATH):
        print(f"❌ '{GOLDSQL_PATH}' 파일을 찾을 수 없습니다.")
        return records
    with open(GOLDSQL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            records.append(json.loads(line))
    return records

def load_ddl(instance_id: str) -> str:
    db_dir = os.path.join(parent_dir, "examples", str(instance_id))
    sqlite_files = glob.glob(os.path.join(db_dir, "*.sqlite"))
    if not sqlite_files: return "SCHEMA NOT FOUND"
    try:
        conn = sqlite3.connect(sqlite_files[0])
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        ddls = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return "\n\n".join(ddls)
    except Exception as e:
        return f"Error extracting DDL: {e}"

def get_existing_functional_groups():
    files = glob.glob(os.path.join(SEMANTIC_DIR, "*.yaml"))
    return [os.path.basename(f).replace(".yaml", "") for f in files]

# ==========================================
# 🌟 리스트 병합 및 중복 제거 헬퍼 함수들
# ==========================================
def merge_descriptions(existing, new):
    seen = {f"{d.get('table')}.{d.get('column')}" for d in existing}
    for d in new:
        key = f"{d.get('table')}.{d.get('column')}"
        if key not in seen and d.get('table') and d.get('column'):
            existing.append(d)
            seen.add(key)

def merge_relations(existing, new):
    seen = {f"{r.get('table_1')}.{r.get('column_1')}-{r.get('table_2')}.{r.get('column_2')}" for r in existing}
    for r in new:
        key = f"{r.get('table_1')}.{r.get('column_1')}-{r.get('table_2')}.{r.get('column_2')}"
        if key not in seen and r.get('table_1'):
            existing.append(r)
            seen.add(key)

def merge_synonyms(existing, new):
    seen = {s.get('nl_term').lower() for s in existing if s.get('nl_term')}
    for s in new:
        if s.get('nl_term') and s.get('nl_term').lower() not in seen:
            existing.append(s)
            seen.add(s.get('nl_term').lower())

def merge_biz_logic(existing, new):
    seen = {b.get('metric_name').lower() for b in existing if b.get('metric_name')}
    for b in new:
        if b.get('metric_name') and b.get('metric_name').lower() not in seen:
            existing.append(b)
            seen.add(b.get('metric_name').lower())


def build_functional_semantics():
    records = load_gold_sqls()
    print(f"🚀 총 {len(records)}개의 Gold SQL을 분석하여 기능 단위로 통합합니다...")

    for record in records:
        instance_id = record.get('instance_id')
        question = record.get('question')
        gold_sql = record.get('gold_sql')
        db_id = record.get('db', 'unknown_db')
        
        ddl_context = load_ddl(instance_id)
        existing_groups = get_existing_functional_groups()
        
        print(f"\n⚙️ {instance_id} 분석 중 (DB: {db_id})...")
        
        # 💡 [프롬프트 핵심 변경]: 너무 잘게 쪼개지지 않도록 분석 의도/유형 중심으로 묶도록 지시
        prompt = f"""
        You are an expert Data Architect. Analyze the Query, SQL, and DDL.
        Categorize this into a "functional_group".
        
        [CRITICAL: Functional Group Categorization Rules]
        1. CONSOLIDATE BY ANALYTICAL INTENT: Even if the database names or specific table names differ, if the analytical intent (e.g., calculating revenue, user activity, product performance) and schema patterns are similar, merge them into the SAME functional group.
        2. PREVENT OVER-SEGMENTATION: Do NOT create highly specific groups like 'ecommerce_customer_retention' and 'bank_customer_retention'. Merge them into a single abstract group like 'customer_retention_analysis' or 'user_behavior'.
        3. AVOID EXTREME BLOAT: While merging is encouraged, do not put completely unrelated domains together (e.g., 'baseball_player_stats' and 'hospital_patient_records' should remain separate).
        4. REUSE EXISTING GROUPS FIRST: Strongly prefer categorizing the input into one of the 'Existing Groups' provided below before inventing a new one.
        
        Existing Groups: {existing_groups}
        
        [SQL Generation Rules for Derived Metrics / Business Logic]
        1. DO NOT write a single, long, deeply nested SQL query.
        2. If the logic is complex, break it down into shorter, logical blocks using CTEs (WITH clauses).
        3. Ensure no single line of SQL code exceeds 80 characters. Insert line breaks (`\n`) appropriately for readability.
        4. Capitalize all SQL keywords (SELECT, FROM, WHERE, GROUP BY, etc.).
        
        [CRITICAL JSON FORMATTING RULES]
        1. Escape ALL internal double quotes within strings using a backslash.
        2. DO NOT include trailing commas at the end of lists or objects.
        3. Return ONLY the JSON object.
        
        Extract the knowledge into the following strict JSON schema:
        {{
            "functional_group": "string (snake_case, representing core analytical intent)",
            "descriptions": [{{"table": "...", "column": "...", "meaning": "..."}}],
            "relations": [{{"table_1": "...", "column_1": "...", "table_2": "...", "column_2": "...", "meaning": "..."}}],
            "synonyms": [{{"nl_term": "...", "db_target": "...", "type": "value|column|condition"}}],
            "biz_logic": [{{"metric_name": "...", "sql_logic": "..."}}]
        }}

        [DDL]
        {ddl_context}

        [Input]
        Question: {question}
        SQL: {gold_sql}
        """
        
        try:
            llm_params = {
                "messages": [{"role": "user", "content": prompt}],
                "response_mime_type": "application/json"
            }
            
            is_success, response_text = call_llm(llm_params)
            
            if not is_success:
                print(f" ⚠️ LLM 호출 API 에러: {response_text}")
                continue
            
            # JSON 파싱 및 복구 (json-repair 활용)
            parsed_intent = {}
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                try:
                    parsed_intent = repair_json(json_str, return_objects=True)
                    if not parsed_intent:
                        raise ValueError("파싱된 JSON이 비어 있습니다.")
                except Exception as e:
                    print(f" ⚠️ JSON 파싱 및 복구 에러 (건너뜀): {e}")
                    print(f" 🔍 [디버깅] 실패한 원본 앞/뒤:\n{json_str[:150]} ... {json_str[-150:]}\n")
                    continue
            else:
                print(" ⚠️ LLM 응답에서 JSON 중괄호 구조를 찾을 수 없습니다.")
                continue
            
            if not isinstance(parsed_intent, dict):
                print(f" ⚠️ 파싱 결과가 딕셔너리가 아닙니다. (현재 타입: {type(parsed_intent)})")
                continue
            
            # 파일명 정리
            func_group = parsed_intent.get("functional_group", "uncategorized")
            safe_func_group = "".join([c if c.isalnum() else "_" for c in func_group]).strip("_")
            yaml_path = os.path.join(SEMANTIC_DIR, f"{safe_func_group}.yaml")
            
            # 💡 [핵심] 기존 YAML 로드 시 app.py 연동을 위한 'databases' 배열 기본 할당
            yaml_content = {"databases": [], "descriptions": [], "relations": [], "synonyms": [], "biz_logic": []}
            if os.path.exists(yaml_path):
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_content = yaml.safe_load(f) or yaml_content

            # 💡 [핵심] 현재 분석 중인 DB 이름을 'databases' 배열에 안전하게 추가
            if "databases" not in yaml_content:
                yaml_content["databases"] = []
            if db_id and db_id != "unknown_db" and db_id not in yaml_content["databases"]:
                yaml_content["databases"].append(db_id)

            # 중복 없이 병합 (Merge)
            merge_descriptions(yaml_content.setdefault("descriptions", []), parsed_intent.get("descriptions", []))
            merge_relations(yaml_content.setdefault("relations", []), parsed_intent.get("relations", []))
            merge_synonyms(yaml_content.setdefault("synonyms", []), parsed_intent.get("synonyms", []))
            merge_biz_logic(yaml_content.setdefault("biz_logic", []), parsed_intent.get("biz_logic", []))
            
            # SQL 포매팅
            if "biz_logic" in yaml_content:
                for biz in yaml_content["biz_logic"]:
                    if "sql_logic" in biz:
                        biz["sql_logic"] = format_sql(biz["sql_logic"])
            
            # YAML로 저장
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_content, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
                
            print(f" ✅ [{safe_func_group}] 통합 완료.")

            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f)

        except Exception as e:
            print(f" ❌ {instance_id} 분석 실패 (기타 에러): {e}")
        
if __name__ == "__main__":
    build_functional_semantics()