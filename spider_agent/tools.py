import os
import glob
import logging
from .llm import call_llm
from .prompts import SCHEMA_LINKING_SYSTEM

logger = logging.getLogger("langgraph_agent")

def llm_based_schema_linking(question: str, intent: str, keywords: str, db_id: str) -> str:
    # 1. 최상단의 schemas 폴더 경로
    schema_dir = os.path.join(".", "schemas", db_id) 
    
    # 🌟 수정 2: 해당 도메인 폴더 안에서 .yaml 파일들을 검색합니다.
    yaml_files = glob.glob(os.path.join(schema_dir, "*.yaml"))
    
    if not yaml_files:
        logger.error(f"⚠️ 스키마 폴더({schema_dir})에서 YAML 파일을 찾을 수 없습니다!")
        return "Error: Schema not found."

    all_schemas = []
    for file_path in yaml_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_name = os.path.basename(file_path)
            all_schemas.append(f"--- [File: {file_name}] ---\n{f.read()}")

    combined_schemas = "\n\n".join(all_schemas)

    user_content = (
        f"Original Question: {question}\n"
        f"Target Database: {db_id}\n"
        f"Analyzed Intent: {intent}\n"
        f"Target Keywords: {keywords}\n\n"
        f"Available Database Schemas:\n{combined_schemas}"
    )

    status, response = call_llm({
        #"model": "gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": SCHEMA_LINKING_SYSTEM},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        #"max_tokens": 4000
    })

    return response.strip() if status else combined_schemas