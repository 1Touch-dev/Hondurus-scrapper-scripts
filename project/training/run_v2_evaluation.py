import json
import os
import time
import re
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv('project/.env')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

BASE_MODEL = "gpt-4o-mini-2024-07-18"

def load_models():
    with open("project/config/model_registry.json", "r") as f:
        registry = json.load(f)
    return registry["fine_tuned_model"], registry["fine_tuned_model_v2"]

V1_MODEL, V2_MODEL = load_models()

def get_eval_prompts_v2():
    prompts = []
    # 20 Political Investigations
    topics_pol = ["financial corruption in the construction of the San José bridge", "misuse of emergency funds during the pandemic in the Northern region", "nepotism in the appointment of judicial officials in Tegucigalpa", "illegal land seizures by developers in the Lenca territory", "unreported campaign financing from questionable sources in the 2021 elections"]
    for t in topics_pol:
        prompts.append({"category": "political_investigation", "system": "[COUNTRY=Honduras]\n[DOMAIN=political_investigation]\n[OUTLET=criterio.hn]\n[TASK=article_generation]", "user": f"Write an investigative journalism article about {t}."})
    
    # 20 Natural Disasters
    topics_nat = ["impact of drought on coffee plantations in El Paraíso", "recovery efforts in La Lima after historic flooding", "landslide risks in the urban hillsides of Tegucigalpa", "illegal logging increasing forest fire susceptibility in Olancho", "coastal erosion threatening tourism infrastructure in Trujillo"]
    for t in topics_nat:
        prompts.append({"category": "natural_disasters", "system": "[COUNTRY=Honduras]\n[DOMAIN=mainstream_news]\n[OUTLET=laprensa.hn]\n[TASK=article_generation]", "user": f"Write a news report about {t}."})

    # 20 Sports
    topics_spt = ["the rising young talent in the Honduran National League", "stadium safety concerns during the national classic match", "Olimpia's historical performance in CONCACAF tournaments", "Honduran athletes preparing for the Olympic qualifiers", "the economic impact of match-day events on local vendors"]
    for t in topics_spt:
        prompts.append({"category": "sports", "system": "[COUNTRY=Honduras]\n[DOMAIN=sports]\n[OUTLET=diez.hn]\n[TASK=article_generation]", "user": f"Write a sports article about {t}."})

    # 20 Economic News
    topics_eco = ["the volatility of the Lempira against the Dollar", "new export opportunities for Honduran textiles in Europe", "the role of remittances in supporting rural communities", "challenges faced by small entrepreneurs in San Pedro Sula", "investment in renewable energy projects in Southern Honduras"]
    for t in topics_eco:
        prompts.append({"category": "economic_news", "system": "[COUNTRY=Honduras]\n[DOMAIN=mainstream_news]\n[OUTLET=elheraldo.hn]\n[TASK=article_generation]", "user": f"Write an article about {t}."})

    # 20 Cultural Stories
    topics_cul = ["the culinary traditions of the Garifuna people", "the revival of artisanal pottery in the town of Valle de Ángeles", "the impact of local festivals on community identity", "traditional music education for youth in the Western highlands", "modern Honduran painters gaining international recognition"]
    for t in topics_cul:
        prompts.append({"category": "cultural_stories", "system": "[COUNTRY=Honduras]\n[DOMAIN=cultural_blog]\n[OUTLET=blogs]\n[TASK=article_generation]", "user": f"Write a blog post about {t}."})

    return prompts

def generate_output(model, system, user):
    try:
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=1000,
            temperature=0.7
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def llm_judge_v2(text, category):
    prompt = f"""Evaluate this Honduran journalism article (Spanish). 
    Category: {category}
    
    Article: {text[:2000]}
    
    Provide JSON:
    - tone_accuracy (1-5)
    - structure_quality (1-5)
    - hallucination_rate (1-5, 5 means NO hallucination)
    - vocab_diversity (1-5)
    - has_boilerplate (boolean, true if scraper/UI text found)
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except:
        return {}

def main():
    print("--- STEP 9, 10, 11: Comprehensive Evaluation (100 Prompts) ---")
    prompts = get_eval_prompts_v2()
    results = []
    
    models = {"Base": BASE_MODEL, "v1": V1_MODEL, "v2": V2_MODEL}
    
    for p in tqdm(prompts):
        prompt_results = {"prompt": p["user"], "category": p["category"]}
        for name, mid in models.items():
            out = generate_output(mid, p["system"], p["user"])
            score = llm_judge_v2(out, p["category"])
            prompt_results[name] = {"text": out, "scores": score}
        results.append(prompt_results)
        
    with open("project/outputs/evaluation_outputs_v2.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    # Aggregate metrics
    summary = {}
    for name in models.keys():
        summary[name] = {
            "avg_tone": np.mean([r[name]["scores"].get("tone_accuracy", 3) for r in results]),
            "avg_struct": np.mean([r[name]["scores"].get("structure_quality", 3) for r in results]),
            "avg_hallucination": np.mean([r[name]["scores"].get("hallucination_rate", 3) for r in results]),
            "avg_diversity": np.mean([r[name]["scores"].get("vocab_diversity", 3) for r in results]),
            "boilerplate_count": sum(1 for r in results if r[name]["scores"].get("has_boilerplate", False))
        }
        
    with open("project/outputs/model_comparison_v2.json", "w") as f:
        json.dump(summary, f, indent=4)
        
    print("Evaluation Complete. Results saved to project/outputs/evaluation_outputs_v2.json")

if __name__ == "__main__":
    import numpy as np
    main()
