import json
import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv('project/.env')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_embeddings(texts, model="text-embedding-3-small"):
    # Batch size for embeddings
    batch_size = 50
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        # Ensure no empty strings
        batch = [t if t.strip() else "empty" for t in batch]
        response = client.embeddings.create(input=batch, model=model)
        all_embeddings.extend([e.embedding for e in response.data])
        
    return np.array(all_embeddings)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def deduplicate_dataset():
    print("--- STEP 4: Embedding-Based Deduplication (Threshold 0.92) ---")
    input_file = "project/datasets/dataset_clean_v2.jsonl"
    output_file = "project/datasets/dataset_dedup_v2.jsonl"
    
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
            
    if not records:
        print("No records to deduplicate.")
        return
        
    texts = []
    for r in records:
        assistant_msg = next(m for m in r['messages'] if m['role'] == 'assistant')
        texts.append(assistant_msg['content'])
        
    print(f"Calculating embeddings for {len(texts)} records...")
    embeddings = get_embeddings(texts)
    
    to_keep = []
    dropped_count = 0
    
    indices_to_drop = set()
    
    print("Computing similarity matrix...")
    for i in range(len(embeddings)):
        if i in indices_to_drop:
            continue
            
        for j in range(i + 1, len(embeddings)):
            if j in indices_to_drop:
                continue
                
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim > 0.92:
                indices_to_drop.add(j)
                dropped_count += 1
                
    for i, r in enumerate(records):
        if i not in indices_to_drop:
            to_keep.append(r)
            
    with open(output_file, 'w', encoding='utf-8') as f:
        for r in to_keep:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
            
    print(f"Deduplication complete. Kept {len(to_keep)}/{len(records)} records. Dropped {dropped_count} duplicates.")

if __name__ == "__main__":
    deduplicate_dataset()
