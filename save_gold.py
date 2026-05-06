import os
import json
import subprocess
import shutil
import glob
import argparse
import re
import ast
import pandas as pd
from datetime import datetime
import sys
from openpyxl import load_workbook

# 현재 실행 파일의 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def save_gold_sql(db_id, instance_id, question, gold_sql):
    """
    정답으로 판정된 질의-SQL 쌍을 실행 디렉토리의 gold_sql.jsonl 파일에 통합 저장합니다.[cite: 18]
    형태: {"db": ..., "instance_id": ..., "question": ..., "gold_sql": ...}
    """
    output_file = os.path.join(current_dir, "gold_sql.jsonl")
    
    record = {
        "db": db_id,
        "instance_id": instance_id,
        "question": question,
        "gold_sql": gold_sql
    }
    
    # JSONL 형식으로 한 줄씩 추가(Append) 저장[cite: 18]
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"💾 [Gold SQL 저장] {instance_id} (DB: {db_id})")

def prepare_submission(run_name):
    predictions_file = f"output/{run_name}/predictions.jsonl"
    target_dir = f"../../spider2-lite/evaluation_suite/{run_name}"
    os.makedirs(target_dir, exist_ok=True)
    
    metadata = {}
    with open(predictions_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            instance_id = record.get("instance_id")
            sql = record.get("generated_query", "")
            metadata[instance_id] = {
                "retry_count": record.get("retry_count", 0),
                "step_count": record.get("step_count", 0)
            }
            if instance_id and sql != "ERROR":
                with open(os.path.join(target_dir, f"{instance_id}.sql"), 'w', encoding='utf-8') as sql_file:
                    sql_file.write(sql)
    return metadata

def run_evaluation(run_name):
    eval_suite_dir = "../../spider2-lite/evaluation_suite"
    eval_script = "evaluate.py"
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

def record_to_excel(run_name, dataset_name, output_log, metadata, tc_file_path, excel_file="evaluation_history_v4.xlsx"):
    # 평가 결과 리스트 파싱[cite: 18]
    dict_match = re.search(r"(\{'.*?\})", output_log)
    individual_results = {}
    if dict_match:
        try:
            individual_results = ast.literal_eval(dict_match.group(1))
        except Exception as e:
            print(f"⚠️ 결과 파싱 오류: {e}")

    # 💡 [추가] local_tc.jsonl에서 실제 질문(Question) 매핑 데이터 로드
    tc_mapping = {}
    if os.path.exists(tc_file_path):
        with open(tc_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                tc_data = json.loads(line)
                tc_mapping[tc_data["instance_id"]] = tc_data["question"]
        print(f"📖 [질문 로드 완료] 파일: {tc_file_path} (총 {len(tc_mapping)}개)")
    else:
        print(f"⚠️ [주의] 질문 파일을 찾을 수 없습니다: {tc_file_path}")

    # 정답 TC 대상 Gold SQL 추출 프로세스[cite: 18]
    print(f"\n✨ 정답 TC 대상 Gold SQL 추출 및 통합 저장 시작...")
    predictions_file = f"output/{run_name}/predictions.jsonl"
    
    if os.path.exists(predictions_file):
        with open(predictions_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                record = json.loads(line)
                iid = record.get("instance_id")
                
                # 평가 결과가 1(정답)인 경우에만 저장 로직 가동[cite: 18]
                if individual_results.get(iid) == 1:
                    # 💡 predictions.jsonl에 질문이 없으면 tc_mapping에서 가져옴
                    nl_question = record.get("question") or tc_mapping.get(iid, "")
                    correct_sql = record.get("generated_query", "")
                    
                    # db_id 추출[cite: 18]
                    db_id = record.get("db") or record.get("db_id")
                    if not db_id and iid:
                        db_id = iid.split("_")[0]
                    if not db_id:
                        db_id = dataset_name 
                    
                    # 통합 gold_sql.jsonl 파일에 저장[cite: 18]
                    save_gold_sql(db_id, iid, nl_question, correct_sql)
    else:
        print(f"⚠️ 예측 파일({predictions_file})이 없습니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name", type=str, nargs="?", default="latest_run", help="실험 이름")
    parser.add_argument("--dataset", type=str, default="General", help="데이터셋 이름")
    # 💡 [추가] 질문 원본 파일 경로를 입력받는 인자
    parser.add_argument("--tc_file", type=str, default="testset/local_tc.jsonl", help="질문 원본 jsonl 파일 경로")
    args = parser.parse_args()
    
    metadata = prepare_submission(args.run_name)
    result_log = run_evaluation(args.run_name)
    
    if result_log:
        # 💡 tc_file 경로를 함께 전달
        record_to_excel(args.run_name, args.dataset, result_log, metadata, args.tc_file)