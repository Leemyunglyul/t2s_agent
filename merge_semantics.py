import json
import os
import re
import argparse
import yaml
from collections import defaultdict
from spider_agent.llm import call_llm

# 💡 [프롬프트 수정] 중복 배제 및 절대적 단일화 지침 강화
MERGE_PROMPT = """
You are an expert Database Architect and Knowledge Base Curator.
Your task is to merge several Semantic Models into a SINGLE, pristine, and ABSOLUTELY NON-REDUNDANT YAML document.

# ⚠️ YAML SYNTAX SAFETY RULES (CRITICAL):
1. USE BLOCK SCALARS: Always use the literal block scalar symbol '|' for 'meaning' and 'sql_logic' fields. This prevents errors when the text contains colons (:), quotes, or special characters.
2. QUOTE STRING FIELDS: Always wrap 'nl_term', 'db_target', 'table', and 'column' values in double quotes (" ") to ensure valid parsing.
3. INDENTATION: Use strictly 2-space indentation. Ensure all list items ('-') are aligned correctly.
4. NO IN-LINE COLONS: Never write a colon within a string unless the entire string is quoted or starts with a block scalar.

# ABSOLUTE ZERO REDUNDANCY MANDATE:
1. NO DUPLICATE ENTRIES: You are strictly forbidden from listing the same table, column, relationship, or metric more than once.
2. UNIQUE KEYS:
   - 'descriptions': There must be exactly ONE entry per unique (table, column) pair.
   - 'relations': There must be exactly ONE entry per unique connection between two columns.
   - 'biz_logic': There must be exactly ONE entry per unique 'metric_name'.
3. SEMANTIC MERGING: If multiple sources provide information for the same element, combine their insights into a single, comprehensive, and high-density description. Do not repeat facts.
4. PRUNE TRIVIALITY: Remove all redundant or obvious information (e.g., "ID is the identifier"). Keep only high-value business logic and hidden relations.
5. BASELINE OVERRIDE: Treat the 'EXISTING BASELINE' as the primary truth. Only add information from 'New Sources' if it provides a NEW insight or a BETTER definition. If the new info is already covered, DISCARD IT.

# OUTPUT FORMAT:
You MUST output ONLY valid YAML inside a ```yaml code block.

descriptions:
  - table: ...
    column: ...
    meaning: "Merged, concise, and non-repetitive business meaning."
relations:
  - table_1: ...
    column_1: ...
    table_2: ...
    column_2: ...
synonyms:
  - nl_term: "term1, term2, term3" # Group multiple synonyms into one line
    db_target: ...
    type: "..."
biz_logic:
  - metric_name: ...
    sql_logic: "Single optimized SQL formula."
"""

def merge_semantic_models(input_jsonl):
    db_to_instances = defaultdict(list)
    
    # 1. JSONL 읽어서 DB별로 instance_id 그룹화
    print(f"📖 입력 파일 읽는 중: {input_jsonl}")
    with open(input_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            db_id = record.get("db") or record.get("db_id")
            instance_id = record.get("instance_id")
            if db_id and instance_id:
                db_to_instances[db_id].append(instance_id)
                
    # 💡 [수정] 현재 실행 파일 기준 ./semantic_models 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    semantic_dir = os.path.join(current_dir, "semantic_models")
    os.makedirs(semantic_dir, exist_ok=True)
    
    for db_id, instances in db_to_instances.items():
        print(f"\n🔄 DB [{db_id}] 시맨틱 모델 통합/업데이트 시작...")
        
        combined_yaml_text = ""
        
        # 💡 [신규] 기존 통합 파일이 있으면 베이스라인으로 읽어옴
        unified_path = os.path.join(semantic_dir, f"{db_id}.yaml")
        if os.path.exists(unified_path):
            print(f"  - 📂 기존 통합 모델 발견 ({db_id}.yaml). 이를 기반으로 병합합니다.")
            with open(unified_path, 'r', encoding='utf-8') as uf:
                combined_yaml_text += f"\n# --- EXISTING BASELINE UNIFIED MODEL ---\n"
                combined_yaml_text += uf.read() + "\n"

        found_new_count = 0
        unique_instances = set(instances)
        for iid in unique_instances:
            yaml_path = os.path.join(semantic_dir, f"{iid}.yaml")
            if os.path.exists(yaml_path):
                with open(yaml_path, 'r', encoding='utf-8') as yf:
                    combined_yaml_text += f"\n# --- New Source: {iid} ---\n"
                    combined_yaml_text += yf.read() + "\n"
                found_new_count += 1
                
        if found_new_count == 0 and not os.path.exists(unified_path):
            print(f"⚠️ [{db_id}] 통합할 신규 또는 기존 데이터가 없습니다. 건너뜁니다.")
            continue
            
        print(f"  - 신규 {found_new_count}개 파일 추가. LLM 최적화 병합 중...")
        
        # 3. LLM에게 병합 및 최적화(Bloat Control) 요청
        status, response = call_llm({
            "model": "gemini-2.5-pro",
            "messages": [
                {"role": "system", "content": MERGE_PROMPT},
                {"role": "user", "content": f"Update and optimize the semantic model for DB '{db_id}'. Ensure ABSOLUTELY NO DUPLICATES:\n{combined_yaml_text}"}
            ],
            "temperature": 0.0
        })
        
        if status and response:
            match = re.search(r'```(?:yaml)?\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
            final_yaml = match.group(1).strip() if match else response.strip()
            
            with open(unified_path, 'w', encoding='utf-8') as out_f:
                out_f.write(final_yaml)
            print(f"✅ [{db_id}] 통합 및 최적화 완료! 저장 경로: {unified_path}")
        else:
            print(f"❌ [{db_id}] LLM 호출 실패")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DB별 시맨틱 모델 통합 및 최적화 스크립트")
    parser.add_argument("input_jsonl", type=str, help="통합 기준이 될 JSONL 파일 경로")
    args = parser.parse_args()
    
    merge_semantic_models(args.input_jsonl)