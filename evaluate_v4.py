import os
import json
import subprocess
import shutil
import glob
import argparse
import re
import ast
import sqlite3
import pandas as pd
import yaml
from datetime import datetime
import sys
from openpyxl import load_workbook
import os

# 💡 [경로 수정] 현재 파일(testset/evaluate_v4.py)의 부모 디렉토리를 path에 추가하여
# spider_agent 폴더의 모듈들을 정상적으로 import 할 수 있게 합니다.
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from spider_agent.llm import call_llm
from spider_agent.prompts import SEMANTIC_EXTRACTOR_SYSTEM

def get_schema_ddl(db_id):
    """
    .py 파일과 동일 선상에 있는 examples 폴더 내의 
    sqlite 파일로부터 실제 DDL을 추출하는 헬퍼 함수
    """
    # 💡 [수정] current_dir 아래의 examples를 바로 지정
    db_dir = os.path.join(current_dir, "examples", db_id)
    sqlite_files = glob.glob(os.path.join(db_dir, "*.sqlite"))
    
    if not sqlite_files:
        print(f"⚠️ DB 파일을 찾을 수 없습니다: {db_dir}")
        return "SCHEMA NOT FOUND"
    
    db_path = sqlite_files[0]
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        ddls = [row[1] for row in cursor.fetchall() if row[1]]
        conn.close()
        return "\n\n".join(ddls)
    except Exception as e:
        print(f"⚠️ DDL 추출 중 에러 발생 ({db_id}): {e}")
        return f"Error extracting DDL: {e}"

def extract_and_merge_semantic_model(db_id, instance_id, nl_question, correct_sql, schema_ddl):
    """기존 YAML을 읽어 LLM에게 큐레이션(정제/추가/삭제)을 맡기고 덮어쓰는 함수"""
    
    semantic_dir = os.path.join(current_dir, "semantic_models")
    os.makedirs(semantic_dir, exist_ok=True)
    yaml_path = os.path.join(semantic_dir, f"{instance_id}.yaml")
    
    existing_model_str = "{}"
    if os.path.exists(yaml_path):
        print(f"🔍 [{instance_id}] 기존 시맨틱 모델 발견. AI 큐레이터가 최적화 및 병합을 시작합니다...")
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                # YAML을 읽어서 LLM에게 주기 위해 JSON 문자열 형태로 변환
                loaded_model = yaml.safe_load(f)
                if loaded_model:
                    existing_model_str = json.dumps(loaded_model, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 기존 YAML 읽기 실패: {e}")
    else:
        print(f"🔍 [{instance_id}] 정답 SQL 역추적 시맨틱 추출 중 (신규 생성)...")
    
    user_content = (
        f"NL Question: {nl_question}\n\n"
        f"Correct SQL:\n{correct_sql}\n\n"
        f"Schema DDL:\n{schema_ddl}\n\n"
        f"Existing Semantic Model:\n{existing_model_str}"
    )
    
    status, response = call_llm({
        "model": "gemini-2.5-pro", 
        "messages": [
            {"role": "system", "content": SEMANTIC_EXTRACTOR_SYSTEM},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        "response_mime_type": "application/json"
    })
    
    if status and response:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            extracted_data = json.loads(match.group(0)) if match else json.loads(response)
            
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(extracted_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                
            print(f"✨ [{instance_id}] 시맨틱 모델(YAML) AI 정제 및 저장 완료!")
        except Exception as e:
            print(f"⚠️ 시맨틱 큐레이션 파싱 에러: {e}")

def prepare_submission(run_name):
    predictions_file = f"output/{run_name}/predictions.jsonl"
    csv_source_dir = f"output/{run_name}/csv_results"
    target_dir = f"../../spider2-lite/evaluation_suite/{run_name}"
    
    print(f"📦 [{run_name}] 평가 데이터 세팅 중...")
    os.makedirs(target_dir, exist_ok=True)
    
    metadata = {} 
    
    with open(predictions_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            instance_id = record.get("instance_id")
            sql = record.get("generated_query", "")
            
            retry_count = record.get("retry_count", 0)
            step_count = record.get("step_count", 0) 
            
            metadata[instance_id] = {
                "retry_count": retry_count,
                "step_count": step_count
            }
            
            if instance_id and sql != "ERROR":
                with open(os.path.join(target_dir, f"{instance_id}.sql"), 'w', encoding='utf-8') as sql_file:
                    sql_file.write(sql)
    
    csv_files = glob.glob(os.path.join(csv_source_dir, "*", "*.csv"))
    csv_count = 0
    for csv_path in csv_files:
        shutil.copy2(csv_path, os.path.join(target_dir, os.path.basename(csv_path)))
        csv_count += 1
            
    print(f"✅ 총 {csv_count}개의 CSV 결과와 SQL을 {target_dir} 폴더로 복사했습니다.")
    
    return metadata 

def run_evaluation(run_name):
    eval_suite_dir = "../../spider2-lite/evaluation_suite"
    eval_script = "evaluate.py"
    
    print(f"\n🚀 공식 평가 스크립트 가동 (Experiment: {run_name})\n" + "="*50)
    
    cmd = ["python", eval_script, "--result_dir", run_name, "--mode", "exec_result"]
    
    output_log = ""
    try:
        process = subprocess.Popen(cmd, cwd=eval_suite_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="")
            output_log += line
        process.wait()
        
        return output_log
    except Exception as e:
        print(f"에러 발생: {e}")
        return ""

def record_to_excel(run_name, dataset_name, output_log, metadata, excel_file="evaluation_history_v4.xlsx"):
    print(f"\n📊 TC별 및 고급 지표 상세 기록 중... ({excel_file} -> '{dataset_name}' 시트)")
    
    dict_match = re.search(r"(\{'.*?\})", output_log)
    individual_results = {}
    if dict_match:
        try:
            individual_results = ast.literal_eval(dict_match.group(1))
        except Exception as e:
            print(f"⚠️ 딕셔너리 파싱 중 오류가 발생했습니다: {e}")

    total_instances = len(individual_results)
    if total_instances == 0:
        print("⚠️ 평가된 인스턴스가 없습니다.")
        return

    correct_instances = sum(individual_results.values())
    zero_retry_correct = 0
    total_retries = 0
    total_steps = 0

    for iid, is_correct in individual_results.items():
        meta = metadata.get(iid, {"retry_count": 0, "step_count": 0})
        total_retries += meta["retry_count"]
        total_steps += meta["step_count"]
        
        if is_correct == 1 and meta["retry_count"] == 0:
            zero_retry_correct += 1

    final_score = round((correct_instances / total_instances) * 100, 2)
    zero_retry_score = round((zero_retry_correct / total_instances) * 100, 2)
    avg_retries = round(total_retries / total_instances, 2)
    avg_steps = round(total_steps / total_instances, 2)

    # 새로 추가할 1줄 데이터 (딕셔너리 형태)
    new_data = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Run Name": run_name,
        "Final Score (%)": final_score,           
        "Zero-Retry Score (%)": zero_retry_score, 
        "Avg Retries": avg_retries,               
        "Avg Steps": avg_steps,                   
        "Correct": correct_instances,
        "Total": total_instances
    }

    # TC별 결과 (local064: 1, local074: 0 ...) 추가
    for tc_id in sorted(individual_results.keys()):
        new_data[tc_id] = individual_results[tc_id]

    new_row_df = pd.DataFrame([new_data])

    # 💡 [핵심 수정] 서식 유지를 위한 openpyxl append 방식 사용
    if not os.path.exists(excel_file):
        # 파일이 아예 없으면 처음 생성 (이때는 서식이 없음)
        new_row_df.to_excel(excel_file, sheet_name=dataset_name, index=False, engine="openpyxl")
    else:
        # 파일이 존재하면 서식을 유지하기 위해 openpyxl을 직접 제어
        try:
            book = load_workbook(excel_file)
            
            if dataset_name not in book.sheetnames:
                # 시트가 없으면 새 시트로 생성
                with pd.ExcelWriter(excel_file, engine="openpyxl", mode='a') as writer:
                    new_row_df.to_excel(writer, sheet_name=dataset_name, index=False)
            else:
                # 1. 대상 시트 가져오기
                sheet = book[dataset_name]
                
                # 2. 현재 시트에 적혀있는 헤더(Column명) 읽어오기
                existing_headers = [cell.value for cell in sheet[1]]
                
                # 3. 새로운 데이터(new_data)에 기존에 없던 TC 열이 생겼을 수 있으므로 헤더 점검 및 확장
                for col in new_row_df.columns:
                    if col not in existing_headers:
                        existing_headers.append(col)
                        sheet.cell(row=1, column=len(existing_headers), value=col)
                
                # 4. 헤더 순서에 맞춰 데이터를 리스트로 변환 (빈 값은 빈 문자열로 처리)
                row_data = []
                for header in existing_headers:
                    row_data.append(new_data.get(header, ""))
                
                # 5. 시트의 맨 아래(max_row + 1)에 데이터만 쏙 밀어넣기
                sheet.append(row_data)
                
                # 6. 서식을 건드리지 않고 파일 저장
                book.save(excel_file)
        
        except Exception as e:
            print(f"⚠️ 엑셀 서식 유지 저장 중 오류 발생: {e}")
            print("대안: 기존 pandas 덮어쓰기 방식으로 저장합니다.")
            # 오류 발생 시 폴백(안전망)으로 기존 pandas 저장 방식 사용
            with pd.ExcelWriter(excel_file, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
                 new_row_df.to_excel(writer, sheet_name=dataset_name, index=False, header=False, startrow=writer.sheets[dataset_name].max_row)

            
    print(f"✅ 평가 지표 기록 완료! (Final: {final_score}%, 1-Shot: {zero_retry_score}%, Avg Retries: {avg_retries}, Avg Steps: {avg_steps})")

    # 💡 [핵심] 엑셀 기록 후, 정답 TC 대상 시맨틱 모델 추출 프로세스
    print(f"\n🧠 정답 TC 대상 시맨틱(Semantic) 프로세스 시작...")
    
    predictions_file = f"output/{run_name}/predictions.jsonl"
    if os.path.exists(predictions_file):
        with open(predictions_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                record = json.loads(line)
                iid = record.get("instance_id")
                
                # 평가 결과가 1(정답)인 경우에만 추출 로직 가동
                if individual_results.get(iid) == 1:
                    nl_question = record.get("question", "")
                    correct_sql = record.get("generated_query", "")
                    
                    # db_id 추출: record에 없으면 instance_id의 첫 번째 부분(ex: local070)을 파싱
                    db_id = record.get("db_id")
                    if not db_id and iid:
                        db_id = iid.split("_")[0] # 보통 local070_123 이라면 앞부분이 db_id
                    if not db_id:
                        db_id = dataset_name 
                    
                    # 로컬 DB 파일에서 DDL 직접 추출
                    schema_ddl = get_schema_ddl(db_id)
                    
                    extract_and_merge_semantic_model(db_id, iid, nl_question, correct_sql, schema_ddl)
    else:
        print(f"⚠️ 예측 파일({predictions_file})을 찾을 수 없어 시맨틱 추출을 건너뜁니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name", type=str, nargs="?", default="latest_run", help="평가할 실험 이름")
    parser.add_argument("--dataset", type=str, default="General", help="엑셀에 기록될 시트 이름 (예: bank, city, ipl)")
    args = parser.parse_args()
    
    metadata = prepare_submission(args.run_name)
    result_log = run_evaluation(args.run_name)
    
    if result_log:
        record_to_excel(args.run_name, args.dataset, result_log, metadata)