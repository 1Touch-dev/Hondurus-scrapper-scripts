import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv('project/.env')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_synthetic_articles():
    print("--- STEP 6: Generating 80 Synthetic Training Examples ---")
    output_file = "project/datasets/dataset_synthetic_v2.jsonl"
    
    categories = {
        "investigative journalism": {"domain": "political_investigation", "outlet": "criterio.hn"},
        "sports journalism": {"domain": "sports", "outlet": "diez.hn"},
        "breaking news": {"domain": "mainstream_news", "outlet": "laprensa.hn"},
        "cultural blog": {"domain": "cultural_blog", "outlet": "blogs"}
    }
    
    # 20 per category = 80 total
    total_to_gen = 80
    per_cat = 20
    
    synthetic_records = []
    
    for cat_name, info in categories.items():
        print(f"Generating {per_cat} examples for {cat_name}...")
        for i in range(per_cat):
            # Dynamic prompt to avoid identical articles
            prompt = f"Write a premium {cat_name} article for a Honduran audience. Topic should be specific to Honduras. Output in Spanish."
            
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"[COUNTRY=Honduras]\n[DOMAIN={info['domain']}]\n[OUTLET={info['outlet']}]\n[TASK=article_generation]"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.8
                )
                article_text = res.choices[0].message.content
                
                record = {
                    "messages": [
                        {"role": "system", "content": f"[COUNTRY=Honduras]\n[DOMAIN={info['domain']}]\n[OUTLET={info['outlet']}]\n[TASK=article_generation]"},
                        {"role": "user", "content": f"Write {info['domain'].replace('_', ' ')} in the editorial voice of {info['outlet']}. Topic: {cat_name} generator {i}"},
                        {"role": "assistant", "content": article_text}
                    ]
                }
                synthetic_records.append(record)
            except Exception as e:
                print(f"Error generating {cat_name} record {i}: {e}")
                
    with open(output_file, 'w', encoding='utf-8') as f:
        for r in synthetic_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
            
    print(f"Generated {len(synthetic_records)} synthetic records. Saved to {output_file}.")

if __name__ == "__main__":
    generate_synthetic_articles()
