import os
import json
import subprocess
import shutil
import glob
import argparse
import re
import ast
from datetime import datetime
import pandas as pd

def prepare_submission(run_name):
    predictions_file = f"output/{run_name}/predictions.jsonl"
    csv_source_dir = f"output/{run_name}/csv_results"
    target_dir = f"../../spider2-lite/evaluation_suite/{run_name}"
    
    print(f"📦 [{run_name}] 평가 데이터 세팅 중...")
    os.makedirs(target_dir, exist_ok=True)
    
    metadata = {} # 💡 메타데이터 저장 딕셔너리
    
    with open(predictions_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            instance_id = record.get("instance_id")
            sql = record.get("generated_query", "")
            
            # 💡 메타데이터 추출 (retry_count와 step_count 모두 가져옴)
            retry_count = record.get("retry_count", 0)
            step_count = record.get("step_count", 0) # 👈 step_count 추가
            
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

def record_to_excel(run_name, dataset_name, output_log, metadata, excel_file="evaluation_history_v3.xlsx"):
    print(f"\n📊 TC별 및 고급 지표 상세 기록 중... ({excel_file} -> '{dataset_name}' 시트)")
    
    # 1. 개별 TC 결과 추출
    dict_match = re.search(r"(\{'.*?\})", output_log)
    individual_results = {}
    if dict_match:
        try:
            individual_results = ast.literal_eval(dict_match.group(1))
        except Exception as e:
            print(f"⚠️ 딕셔너리 파싱 중 오류가 발생했습니다: {e}")

    # 2. 고급 지표 계산 로직 💡
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
        
        # 정답이면서 재시도 횟수가 0인 경우 (원샷 정답)
        if is_correct == 1 and meta["retry_count"] == 0:
            zero_retry_correct += 1

    final_score = round((correct_instances / total_instances) * 100, 2)
    zero_retry_score = round((zero_retry_correct / total_instances) * 100, 2)
    avg_retries = round(total_retries / total_instances, 2)
    avg_steps = round(total_steps / total_instances, 2)

    # 3. 데이터프레임 구성 💡 (Retry와 Step 모두 포함)
    new_data = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Run Name": run_name,
        "Final Score (%)": final_score,           # 최종 성공률
        "Zero-Retry Score (%)": zero_retry_score, # 1회차 정답률
        "Avg Retries": avg_retries,               # 평균 재시도 횟수 (0에 가까울수록 똑똑함)
        "Avg Steps": avg_steps,                   # 평균 스텝 수 (비용 및 지연시간 지표)
        "Correct": correct_instances,
        "Total": total_instances
    }

    for tc_id in sorted(individual_results.keys()):
        new_data[tc_id] = individual_results[tc_id]

    new_row_df = pd.DataFrame([new_data])

    # 4. 엑셀 읽기 및 병합
    sheets_dict = {}
    if os.path.exists(excel_file):
        sheets_dict = pd.read_excel(excel_file, sheet_name=None)
    
    target_sheet_df = sheets_dict.get(dataset_name, pd.DataFrame())
    
    if target_sheet_df.empty:
        updated_df = new_row_df
    else:
        updated_df = pd.concat([target_sheet_df, new_row_df], ignore_index=True)
    
    # 5. 시트별 저장
    base_cols = ["Date", "Run Name", "Final Score (%)", "Zero-Retry Score (%)", "Avg Retries", "Avg Steps", "Correct", "Total"]
    tc_cols = sorted([c for c in updated_df.columns if c not in base_cols])
    updated_df = updated_df[base_cols + tc_cols]

    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        for sheet, df in sheets_dict.items():
            if sheet == dataset_name: continue
            df.to_excel(writer, sheet_name=sheet, index=False)
        updated_df.to_excel(writer, sheet_name=dataset_name, index=False)
            
    print(f"✅ 평가 지표 기록 완료! (Final: {final_score}%, 1-Shot: {zero_retry_score}%, Avg Retries: {avg_retries}, Avg Steps: {avg_steps})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name", type=str, nargs="?", default="latest_run", help="평가할 실험 이름")
    parser.add_argument("--dataset", type=str, default="General", help="엑셀에 기록될 시트 이름 (예: bank, city, ipl)")
    args = parser.parse_args()
    
    metadata = prepare_submission(args.run_name)
    result_log = run_evaluation(args.run_name)
    
    if result_log:
        record_to_excel(args.run_name, args.dataset, result_log, metadata)