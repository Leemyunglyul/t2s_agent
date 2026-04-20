import json
import os
import logging
import argparse
import shutil
import glob
from datetime import datetime
from spider_agent.graphs import build_agent_graph

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "T2S-Agent"

def setup_global_logging(run_name: str):
    log_dir = os.path.join(".", "output", run_name, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 파일명 형식: output/테스트이름/logs/_global_테스트이름_시간.log
    log_filename = os.path.join(log_dir, f"_global_{run_name}_{current_time}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s',
        force=True,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("batch_executor")
    
agent_app = build_agent_graph()

def setup_instance_logger(instance_id: str, run_name: str) -> logging.FileHandler:
    log_dir = os.path.join(".", "output", run_name, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_path = os.path.join(log_dir, f"{instance_id}.log")
    
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logging.getLogger().addHandler(file_handler)
    return file_handler

def remove_instance_logger(file_handler: logging.FileHandler):
    logging.getLogger().removeHandler(file_handler)
    file_handler.close()

# 💡 [수정] 단순 SQL 문자열이 아니라 final_state 딕셔너리 전체를 반환하도록 변경
def run_single_task(question: str, workspace_path: str, instance_id: str, db_id: str, run_name: str) -> dict:
    """단일 테스트 케이스를 에이전트에 통과시키고 최종 상태(State)를 반환합니다."""
    initial_state = {
        "question": question,
        "working_dir": workspace_path,
        "instance_id": instance_id,
        "db_id": db_id,
        "step_count": 0,
        "retry_count": 0,
        "max_steps": 10,             
        "execution_history": [],      
        "is_final_answer": False,
        "has_error": False,
        "run_name": run_name         
    }
    
    try:
        final_state = agent_app.invoke(
            initial_state, 
            config={"run_name": f"{run_name}_{instance_id}"} 
        )
        return final_state
        
    except Exception as e:
        logger.error(f"에이전트 실행 중 치명적 에러: {e}")
        # 에러 발생 시에도 규격에 맞는 최소한의 state 딕셔너리 반환
        return {
            "has_error": True,
            "observation": f"Exception occurred - {str(e)}",
            "generated_code": "ERROR",
            "retry_count": 0
        }

def run_batch_evaluation(input_jsonl: str, db_base_dir: str, output_jsonl: str, run_name: str):
    """JSONL 파일을 읽어와 전체 테스트 케이스를 순차적으로 실행합니다."""
    
    logger.info(f"🚀 배치 평가 시작! 입력 파일: {input_jsonl}")
    
    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    
    success_count = 0
    total_count = 0

    with open(input_jsonl, 'r', encoding='utf-8') as infile, \
         open(output_jsonl, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            if not line.strip():
                continue
                
            total_count += 1
            task = json.loads(line)
            
            instance_id = task.get("instance_id")
            db_id = task.get("db")
            question = task.get("question")
            
            task_log_handler = setup_instance_logger(instance_id, run_name)
            
            try:
                logger.info(f"\n[{line_num}] 실행 중... ID: {instance_id} | DB: {db_id}")
                
                original_workspace = os.path.join(db_base_dir, instance_id)
                
                # 기본값 세팅 (에러 대비)
                generated_sql = "ERROR: Workspace not found."
                final_retry_count = 0
                has_error = True
                
                if not os.path.exists(original_workspace):
                    logger.warning(f"⚠️ 경고: {original_workspace} 폴더를 찾을 수 없습니다. 건너뜁니다.")
                else:
                    isolated_workspace = os.path.join(".", "output", run_name, "isolated_dbs", instance_id)
                    os.makedirs(isolated_workspace, exist_ok=True)
                    
                    for db_file in glob.glob(os.path.join(original_workspace, "*.sqlite")):
                        shutil.copy(db_file, isolated_workspace)
                    
                    # 💡 [수정] 딕셔너리 형태로 반환된 State 받기
                    final_state = run_single_task(question, isolated_workspace, instance_id, db_id, run_name)
                    
                    # State에서 필요한 정보 추출
                    has_error = final_state.get("has_error", False)
                    final_retry_count = final_state.get("retry_count", 0)
                    generated_sql = final_state.get("generated_code", "").strip()
                    
                    if has_error:
                        error_reason = final_state.get("observation", "Max steps reached or unknown error")
                        generated_sql = f"ERROR: {error_reason}"
                    elif not generated_sql or generated_sql.upper() == "ERROR":
                        generated_sql = "ERROR: No valid SQL generated by agent."
                        has_error = True
                    else:
                        success_count += 1
                
                # 💡 [수정] JSONL 파일에 retry_count 함께 저장
                result_record = {
                    "instance_id": instance_id,
                    "db": db_id,
                    "generated_query": generated_sql,
                    "retry_count": final_retry_count, 
                    "step_count": final_state.get("step_count", 0),
                    "has_error": has_error            
                }
                
                outfile.write(json.dumps(result_record, ensure_ascii=False) + "\n")
                outfile.flush() 
                
                logger.info(f"✅ {instance_id} 완료. (현재 성공: {success_count}/{total_count})")
            
            finally:
                remove_instance_logger(task_log_handler)

    logger.info(f"\n🎉 배치 평가 완료! 총 {total_count}개 중 {success_count}개 쿼리 생성 성공.")
    logger.info(f"결과는 {output_jsonl}에 저장되었습니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LangGraph SQL Agent")

    parser.add_argument("run_name", type=str, nargs="?", default="latest_run", help="Name of the experiment run")
    parser.add_argument("input", type=str, nargs="?", default="./testset/city_legislation.jsonl", help="Input JSONL file")
    args = parser.parse_args()
    
    logger = setup_global_logging(args.run_name)

    INPUT_FILE = args.input
    DB_BASE_DIRECTORY = "./examples" 
    OUTPUT_FILE = f"./output/{args.run_name}/predictions.jsonl"
    
    run_batch_evaluation(INPUT_FILE, DB_BASE_DIRECTORY, OUTPUT_FILE, args.run_name)