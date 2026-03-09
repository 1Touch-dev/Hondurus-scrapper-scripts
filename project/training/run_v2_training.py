import json
import os
import random
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('project/.env')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_v2_training():
    print("--- STEP 7 & 8: Merge, Split, and Train v2 ---")
    
    # 1. Merge
    dedup_file = "project/datasets/dataset_dedup_v2.jsonl"
    synth_file = "project/datasets/dataset_synthetic_v2.jsonl"
    
    records = []
    for fpath in [dedup_file, synth_file]:
        with open(fpath, 'r', encoding='utf-8') as f:
            for line in f:
                records.append(json.loads(line))
                
    print(f"Total merged records: {len(records)}")
    
    # 2. Shuffle and Split
    random.seed(42)
    random.shuffle(records)
    
    split_idx = int(len(records) * 0.9)
    train_records = records[:split_idx]
    val_records = records[split_idx:]
    
    train_file = "project/datasets/train_clean_v2.jsonl"
    val_file = "project/datasets/validation_clean_v2.jsonl"
    
    with open(train_file, 'w', encoding='utf-8') as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
            
    with open(val_file, 'w', encoding='utf-8') as f:
        for r in val_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
            
    # 3. Upload to OpenAI
    print("Uploading files to OpenAI...")
    train_obj = client.files.create(file=open(train_file, "rb"), purpose="fine-tune")
    val_obj = client.files.create(file=open(val_file, "rb"), purpose="fine-tune")
    
    print(f"Train File ID: {train_obj.id}")
    print(f"Val File ID: {val_obj.id}")
    
    # 4. Create Fine-tuning Job
    print("Creating fine-tuning job...")
    job = client.fine_tuning.jobs.create(
        training_file=train_obj.id,
        validation_file=val_obj.id,
        model="gpt-4o-mini-2024-07-18",
        suffix="honduras-news-v2"
    )
    
    print(f"Job Created: {job.id}")
    print(f"Status: {job.status}")
    
    # Save Job ID for monitoring
    with open("project/config/job_registry.json", "w") as f:
        json.dump({"job_id": job.id, "version": "v2"}, f)

if __name__ == "__main__":
    run_v2_training()
