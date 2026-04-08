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
    
    with open(predictions_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            instance_id = record.get("instance_id")
            sql = record.get("generated_query", "")
            
            if instance_id and sql != "ERROR":
                with open(os.path.join(target_dir, f"{instance_id}.sql"), 'w', encoding='utf-8') as sql_file:
                    sql_file.write(sql)
    
    csv_files = glob.glob(os.path.join(csv_source_dir, "*", "*.csv"))
    csv_count = 0
    for csv_path in csv_files:
        shutil.copy2(csv_path, os.path.join(target_dir, os.path.basename(csv_path)))
        csv_count += 1
            
    print(f"✅ 총 {csv_count}개의 CSV 결과와 SQL을 {target_dir} 폴더로 복사했습니다.")

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

def record_to_excel(run_name, dataset_name, output_log, excel_file="evaluation_history.xlsx"):
    """평가 로그를 파싱하여 TC별로 열을 분배하여 엑셀에 기록합니다."""
    
    print(f"\n📊 TC별 상세 기록 중... ({excel_file} -> '{dataset_name}' 시트)")
    
    # 1. 기본 지표 추출 (Final Score, Correct, Total)
    final_match = re.search(r"Final score:\s*([\d.]+),\s*Correct examples:\s*(\d+),\s*Total examples:\s*(\d+)", output_log)
    if not final_match:
        print("⚠️ 평가 로그에서 점수 정보를 찾지 못했습니다.")
        return

    # 2. 데이터프레임 구성을 위한 기본 데이터 세팅
    new_data = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Run Name": run_name,
        "Score (%)": round(float(final_match.group(1)) * 100, 2),
        "Correct": int(final_match.group(2)),
        "Total": int(final_match.group(3))
    }

    # 3. 개별 TC 결과 추출 ({'local064': 0, 'local074': 1, ...}) 후 개별 열(Column)로 매핑
    dict_match = re.search(r"(\{'.*?\})", output_log)
    if dict_match:
        try:
            # 문자열 형태의 딕셔너리를 실제 파이썬 딕셔너리로 안전하게 변환
            individual_results = ast.literal_eval(dict_match.group(1))
            
            # 각 TC ID를 새로운 열(key)로 동적 추가
            for tc_id in sorted(individual_results.keys()):
                new_data[tc_id] = individual_results[tc_id]
        except Exception as e:
            print(f"⚠️ 딕셔너리 파싱 중 오류가 발생했습니다: {e}")

    # DataFrame으로 변환하면 딕셔너리의 key들이 엑셀의 헤더(열)가 됨
    new_row_df = pd.DataFrame([new_data])

    # 4. 기존 엑셀 읽기 및 병합
    sheets_dict = {}
    if os.path.exists(excel_file):
        sheets_dict = pd.read_excel(excel_file, sheet_name=None)
    
    target_sheet_df = sheets_dict.get(dataset_name, pd.DataFrame())
    
    if target_sheet_df.empty:
        updated_df = new_row_df
    else:
        # 기존 시트와 새로운 결과를 행으로 병합 (TC 열이 일치하게 합쳐짐)
        updated_df = pd.concat([target_sheet_df, new_row_df], ignore_index=True)
    
    # 5. 시트별 저장 (열 순서 고정: Date, Run Name, Score, Correct, Total -> local001, local002 순서)
    base_cols = ["Date", "Run Name", "Score (%)", "Correct", "Total"]
    tc_cols = sorted([c for c in updated_df.columns if c not in base_cols])
    updated_df = updated_df[base_cols + tc_cols] # 열 순서 재배치

    # 엑셀 파일 저장
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        for sheet, df in sheets_dict.items():
            if sheet == dataset_name: continue # 현재 업데이트 중인 시트는 패스
            df.to_excel(writer, sheet_name=sheet, index=False)
        updated_df.to_excel(writer, sheet_name=dataset_name, index=False)
            
    print(f"✅ TC별 칸 분배 완료! (현재 '{dataset_name}' 시트 컬럼 수: {len(updated_df.columns)}개)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name", type=str, nargs="?", default="latest_run", help="평가할 실험 이름")
    parser.add_argument("--dataset", type=str, default="General", help="엑셀에 기록될 시트 이름 (예: bank, city, ipl)")
    args = parser.parse_args()
    
    # 1. 파일 세팅
    prepare_submission(args.run_name)
    
    # 2. 평가 돌리고 출력 문자열 받기
    result_log = run_evaluation(args.run_name)
    
    # 3. 엑셀에 파싱해서 저장하기
    if result_log:
        record_to_excel(args.run_name, args.dataset, result_log)