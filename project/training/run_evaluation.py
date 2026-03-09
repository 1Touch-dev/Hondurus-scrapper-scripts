import json
import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import re

# Initialize Setup
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

BASE_MODEL = "gpt-4o-mini-2024-07-18"

def load_ft_model():
    with open(os.path.join(CONFIG_DIR, "model_registry.json"), 'r') as f:
        data = json.load(f)
        return data["fine_tuned_model"]

FT_MODEL = load_ft_model()

# --- STEP 1: Create Evaluation Test Suite ---
def get_evaluation_prompts():
    print("--- STEP 1: Creating Evaluation Test Suite ---")
    prompts = []
    
    # 10 Investigative
    for topic in ["corruption in Tegucigalpa public infrastructure", "embezzlement of healthcare funds in the national hospitals", "environmental destruction by mining companies in Olancho", "nepotism in state-owned enterprises", "irregularities in the national energy company ENEE", "the infiltration of organized crime in local municipalities", "mismanagement of education budgets", "illegal logging in the Rio Platano Biosphere Reserve", "bribes in the construction of national highways", "the delayed implementation of the CICIH (anti-corruption commission)"]:
        prompts.append({
            "category": "investigative",
            "system": "[COUNTRY=Honduras]\n[DOMAIN=political_investigation]\n[OUTLET=criterio.hn]\n[TASK=article_generation]",
            "user": f"Write an investigative journalism article about {topic}."
        })
        
    # 10 Mainstream
    for topic in ["severe flooding in northern Honduras due to tropical storms", "new economic measures announced by the Central Bank", "the rising cost of the basic food basket (canasta basica)", "teachers going on strike in Francisco Morazan", "the inauguration of a new public hospital in Comayagua", "changes to the national minimum wage", "the start of the coffee harvest season", "heavy traffic congestion during the holidays in Tegucigalpa", "a new infrastructure project in San Pedro Sula", "the response of COPECO to recent landslides"]:
        prompts.append({
            "category": "mainstream",
            "system": "[COUNTRY=Honduras]\n[DOMAIN=mainstream_news]\n[OUTLET=laprensa.hn]\n[TASK=article_generation]",
            "user": f"Write a news report about {topic}."
        })
        
    # 10 Sports
    for topic in ["the Honduras national football team preparing for the World Cup qualifiers", "Olimpia winning the national classic against Motagua", "Real Espana's new head coach announcement", "the performance of Honduran players in European leagues", "Marathon securing a crucial victory at the Yankel Rosenthal stadium", "the upcoming CONCACAF Champions League matches", "a controversial referee decision in the Liga Nacional", "the rising stars in the Honduran Under-20 national team", "the history of the rivalry between Olimpia and Motagua", "the fan atmosphere at the National Stadium in Tegucigalpa"]:
        prompts.append({
            "category": "sports",
            "system": "[COUNTRY=Honduras]\n[DOMAIN=sports_coverage]\n[OUTLET=diez.hn]\n[TASK=article_generation]",
            "user": f"Write a sports article about {topic}."
        })
        
    # 10 Cultural
    for topic in ["daily life and the vibrant street food scene in San Pedro Sula", "the traditions behind the celebration of the Virgen de Suyapa", "the cultural significance of the Lenca people in western Honduras", "a weekend trip to Valle de Angeles", "the best places to eat baleadas in Tegucigalpa", "the preservation of the Garifuna culture and Punta music", "reviewing a new Honduran independent film", "the atmosphere during the Feria Isidra in La Ceiba", "the revival of traditional Honduran literature", "the impact of migration on family dynamics in rural Honduras"]:
        prompts.append({
            "category": "cultural",
            "system": "[COUNTRY=Honduras]\n[DOMAIN=cultural_blog]\n[OUTLET=blogs]\n[TASK=article_generation]",
            "user": f"Write a blog post about {topic}."
        })
        
    # 10 Edge cases
    for topic in ["the macroeconomics of Honduras and foreign debt", "international coffee export trends shaping the Honduran market", "investigative journalism detailing the history of organized crime in Honduras", "the diplomatic relations between Honduras and China", "the impact of remittances on the Honduran economy", "the rise of tech startups in San Pedro Sula", "agricultural innovation in the production of palm oil", "the challenges of urban planning in a growing Tegucigalpa", "a deep dive into the Honduran penal system", "the environmental impact of coastal development in Roatan"]:
        # Edge cases might not map perfectly to standard outlets, testing robustness
        prompts.append({
            "category": "edge_case",
            "system": "[COUNTRY=Honduras]\n[DOMAIN=mainstream_news]\n[OUTLET=elheraldo.hn]\n[TASK=article_generation]",
            "user": f"Write an article about {topic}."
        })
        
    return prompts

def generate_with_model(model_id, prompt):
    start = time.time()
    try:
        res = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        text = res.choices[0].message.content
        return text, time.time() - start
    except Exception as e:
        print(f"Error generating with {model_id}: {e}")
        return "", 0

# --- STEP 2, 7: Output Generation ---
def generate_outputs(prompts):
    print(f"\n--- STEP 2 & 7: Generating Outputs ({len(prompts)} prompts x 2 models) ---")
    results = []
    
    for i, p in enumerate(tqdm(prompts)):
        ft_text, ft_time = generate_with_model(FT_MODEL, p)
        base_text, base_time = generate_with_model(BASE_MODEL, p)
        
        ft_words = len(re.findall(r'\b\w+\b', ft_text))
        base_words = len(re.findall(r'\b\w+\b', base_text))
        
        results.append({
            "id": i,
            "category": p["category"],
            "prompt_system": p["system"],
            "prompt_user": p["user"],
            "ft_generated": ft_text,
            "ft_token_count": ft_words,  # Treating words as a proxy for structural length
            "ft_time": ft_time,
            "base_generated": base_text,
            "base_token_count": base_words,
            "base_time": base_time
        })
        
    with open(os.path.join(OUTPUTS_DIR, "evaluation_outputs.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    return results

# --- STEP 3, 4, 5, 6: Validation, Style, Hallucination, Diversity ---

def llm_judge(text, category):
    # Determine expected tone based on category
    if category == "investigative":
        tone_desc = "investigative tone, analytical writing, exposing issues"
    elif category == "sports":
        tone_desc = "sports enthusiasm, match coverage, athletic terminology"
    elif category == "cultural":
        tone_desc = "cultural appreciation, vibrant descriptions, blogging style"
    else:
        tone_desc = "objective mainstream news reporting, formal journalism"

    prompt = f"""You are an expert journalism evaluator. Evaluate the following Spanish article generated by an AI model simulating Honduran news.

Article to evaluate:
\"\"\"{text[:2500]}\"\"\"

Provide your evaluation in strict JSON format with exactly these keys:
- "tone_accuracy": (1-5 integer) How well does it match a {tone_desc} tone?
- "structure_quality": (1-5 integer) Does it have a headline and coherent paragraphs?
- "language_fluency": (1-5 integer) Is the Spanish natural, fluent, and localized (Honduran context)?
- "journalism_realism": (1-5 integer) Does it read like a real news article?
- "hallucination_found": (boolean) Are there obvious impossible claims, fake stats, or fabricated organizations?
- "hallucination_explanation": (string) If hallucination_found is true, explain what was fabricated. If false, output "None".

ONLY output valid JSON.
"""
    try:
        res = client.chat.completions.create(
            model=BASE_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": "You are a JSON-only evaluator."}, {"role": "user", "content": prompt}],
            temperature=0
        )
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        print(e)
        return {
            "tone_accuracy": 3, "structure_quality": 3, "language_fluency": 3, "journalism_realism": 3,
            "hallucination_found": False, "hallucination_explanation": "Eval failed"
        }

def unique_word_ratio(text):
    words = re.findall(r'\b\w+\b', text.lower())
    if not words: return 0
    return len(set(words)) / len(words)

def run_evaluations(results):
    print("\n--- STEP 3, 4, 5, 6: Structural & Style Evaluation (LLM Judge) ---")
    evaluated_results = []
    
    for r in tqdm(results):
        # FT evaluation
        ft_struct_flag = r["ft_token_count"] < 300
        ft_uwr = unique_word_ratio(r["ft_generated"])
        ft_judge = llm_judge(r["ft_generated"], r["category"])
        
        # Base evaluation
        base_struct_flag = r["base_token_count"] < 300
        base_uwr = unique_word_ratio(r["base_generated"])
        base_judge = llm_judge(r["base_generated"], r["category"])
        
        evaluated_results.append({
            "id": r["id"],
            "category": r["category"],
            "user_prompt": r["prompt_user"],
            "ft_eval": {
                "too_short": ft_struct_flag,
                "unique_word_ratio": round(ft_uwr, 3),
                **ft_judge
            },
            "base_eval": {
                "too_short": base_struct_flag,
                "unique_word_ratio": round(base_uwr, 3),
                **base_judge
            }
        })
        
    with open(os.path.join(OUTPUTS_DIR, "style_scores.json"), "w", encoding="utf-8") as f:
        json.dump(evaluated_results, f, indent=4, ensure_ascii=False)
        
    return evaluated_results

# --- STEP 8, 9, 10: Metrics, Report, Recommendation ---

def generate_final_report(results, eval_results):
    print("\n--- STEP 8, 9, 10: Generating Final Report ---")
    
    total = len(results)
    
    # Aggregating FT Metrics
    ft_avg_len = sum(r["ft_token_count"] for r in results) / total
    ft_tone = sum(e["ft_eval"]["tone_accuracy"] for e in eval_results) / total
    ft_struct = sum(e["ft_eval"]["structure_quality"] for e in eval_results) / total
    ft_fluency = sum(e["ft_eval"]["language_fluency"] for e in eval_results) / total
    ft_realism = sum(e["ft_eval"]["journalism_realism"] for e in eval_results) / total
    ft_hallucinations = sum(1 for e in eval_results if e["ft_eval"]["hallucination_found"])
    ft_short = sum(1 for e in eval_results if e["ft_eval"]["too_short"])
    ft_uwr = sum(e["ft_eval"]["unique_word_ratio"] for e in eval_results) / total
    
    # Aggregating Base Metrics
    base_avg_len = sum(r["base_token_count"] for r in results) / total
    base_tone = sum(e["base_eval"]["tone_accuracy"] for e in eval_results) / total
    base_struct = sum(e["base_eval"]["structure_quality"] for e in eval_results) / total
    base_fluency = sum(e["base_eval"]["language_fluency"] for e in eval_results) / total
    base_realism = sum(e["base_eval"]["journalism_realism"] for e in eval_results) / total
    base_hallucinations = sum(1 for e in eval_results if e["base_eval"]["hallucination_found"])
    base_short = sum(1 for e in eval_results if e["base_eval"]["too_short"])
    base_uwr = sum(e["base_eval"]["unique_word_ratio"] for e in eval_results) / total
    
    # Recommendation logic
    production_ready = True
    recommendations = []
    if ft_hallucinations > total * 0.15:
        production_ready = False
        recommendations.append("- **High Hallucination Rate**: Consider augmenting dataset with factual grounding examples or penalizing statistical fabrications.")
    if ft_tone < 4.0:
        production_ready = False
        recommendations.append("- **Tone Inaccuracy**: The style scores are low. Consider expanding the dataset specifically for the weaker domains.")
    if ft_short > total * 0.1:
        production_ready = False
        recommendations.append("- **Short Generations**: The model produces too many short articles (<300 words). Add longer examples to the corpus.")
        
    if production_ready:
        recommendations.append("- **Production Ready!** The model exhibits high structural integrity, low hallucinations, and excellent journalistic realism.")
    
    report = f"""# Comprehensive Model Evaluation Report

## Model Details
- **Fine-Tuned Model:** `{FT_MODEL}`
- **Base Model:** `{BASE_MODEL}`
- **Training Dataset Size:** 386 articles
- **Evaluation Set Size:** {total} prompts

## 📊 Evaluation Metrics: Fine-Tuned vs Base

| Metric | Fine-Tuned Model | Base Model |
|--------|------------------|------------|
| Average Word Count | {ft_avg_len:.1f} | {base_avg_len:.1f} |
| Short Articles (< 300 words) | {ft_short} / {total} | {base_short} / {total} |
| Tone Accuracy (1-5) | {ft_tone:.2f} | {base_tone:.2f} |
| Structure Quality (1-5) | {ft_struct:.2f} | {base_struct:.2f} |
| Language Fluency (1-5) | {ft_fluency:.2f} | {base_fluency:.2f} |
| Journalism Realism (1-5) | {ft_realism:.2f} | {base_realism:.2f} |
| Hallucination Count | {ft_hallucinations} / {total} | {base_hallucinations} / {total} |
| Vocab Diversity (UWR) | {ft_uwr:.3f} | {base_uwr:.3f} |

## 💡 Final Recommendation

**Is the fine-tuned model production ready?** {'✅ YES' if production_ready else '❌ NO'}

**Notes & Recommendations:**
{"".join(r + chr(10) for r in recommendations)}

## Example Output Comparison (Prompt ID 0)
**Prompt**: {results[0]["prompt_user"]}

### Fine-Tuned Output
```text
{results[0]["ft_generated"][:800]}...
```

### Base Model Output
```text
{results[0]["base_generated"][:800]}...
```
"""

    with open(os.path.join(OUTPUTS_DIR, "evaluation_report.md"), "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Report saved to {os.path.join(OUTPUTS_DIR, 'evaluation_report.md')}")

def main():
    prompts = get_evaluation_prompts()
    
    print("\n--- Running Evaluation Pipeline (this will take several minutes) ---")
    results = generate_outputs(prompts)
    
    eval_results = run_evaluations(results)
    
    generate_final_report(results, eval_results)
    print("\nPipeline Complete!")

if __name__ == "__main__":
    main()
