import os
import json
import subprocess
import shutil
import glob
import argparse

def prepare_submission(run_name):
    # 경로를 run_name에 맞게 동적으로 설정
    predictions_file = f"output/{run_name}/predictions.jsonl"
    csv_source_dir = f"output/{run_name}/csv_results"
    target_dir = f"../../spider2-lite/evaluation_suite/{run_name}"
    
    print(f"📦 [{run_name}] 평가 데이터 세팅 중...")
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. JSONL 복사
    with open(predictions_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            instance_id = record.get("instance_id")
            sql = record.get("generated_query", "")
            
            if instance_id and sql != "ERROR":
                with open(os.path.join(target_dir, f"{instance_id}.sql"), 'w', encoding='utf-8') as sql_file:
                    sql_file.write(sql)
                    
    # 2. CSV 복사
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

    try:
        process = subprocess.Popen(cmd, cwd=eval_suite_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="")
        process.wait()
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name", type=str, nargs="?", default="latest_run", help="Name of the experiment to evaluate")
    args = parser.parse_args()
    
    prepare_submission(args.run_name)
    run_evaluation(args.run_name)