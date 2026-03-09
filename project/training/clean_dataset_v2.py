import json
import os
import re
from tqdm import tqdm

def clean_text(text):
    boilerplate_patterns = [
        r"Selección de Noticias Más Leídas",
        r"Comparte esto",
        r"Anuncio publicitario",
        r"Noticias relacionadas",
        r"Leer también",
        r"Related article",
        r"También vea",
        r"Siga leyendo",
        r"Haga clic aquí",
        r"Suscríbase",
        r"Síguenos en",
        r"Compartir en:",
        r"Advertisement",
        r"Loading\.\.\.",
        r"Comentarios",
        r"Déjanos tu comentario",
        r"© \d{4} \w+",
        r"Todos los derechos reservados",
        r"Descarga nuestra app",
        r"Visita nuestro sitio",
        r"Relacionados:",
        r"Etiquetas:",
        r"Contenido patrocinado",
        r"Ver todas las entradas"
    ]
    
    # If text is single huge line, split it into sentences and group them
    if '\n' not in text and len(text) > 500:
        # Split by sentence endings
        text = re.sub(r'([\.!\?])\s+([A-Z])', r'\1\n\n\2', text)

    lines = re.split(r'\r?\n', text)
    cleaned_lines = []
    seen_lines = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.lower() in ['facebook', 'twitter', 'instagram', 'whatsapp', 'telegram', 'email', 'print']:
            continue
            
        # Boilerplate check - only for shorter lines to avoid killing the whole article if it's single line
        is_boilerplate = False
        if len(line) < 300:
            for pattern in boilerplate_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    is_boilerplate = True
                    break
        
        if is_boilerplate:
            continue
            
        if line in seen_lines:
            continue
        
        line = re.sub(r'https?://\S+', '', line)
        line = re.sub(r'<[^>]*>', '', line)
        
        words = line.split()
        # Fragments without punctuation that are too short are likely navigation
        if len(words) < 4 and not line.endswith(('.', '!', '?', ':', ')')):
            continue
            
        seen_lines.add(line)
        cleaned_lines.append(line)
    
    return "\n\n".join(cleaned_lines)

def normalize_structure(text):
    lines = text.split('\n\n')
    if len(lines) < 2:
        return ""
    
    word_count = len(text.split())
    if word_count < 100 or word_count > 2000:
        return ""
        
    return text

def clean_dataset_v2():
    print("--- STEP 1 & 2: Aggressive Cleaning ---")
    input_file = "dataset_gpt_finetune.jsonl"
    output_temp = "project/datasets/dataset_clean_v2_temp.jsonl"
    output_final = "project/datasets/dataset_clean_v2.jsonl"
    
    os.makedirs("project/datasets", exist_ok=True)
    
    cleaned_count = 0
    total_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as fin, open(output_temp, 'w', encoding='utf-8') as fout:
        for line in fin:
            if not line.strip(): continue
            total_count += 1
            try:
                data = json.loads(line)
            except: continue
            
            # Cleaning the assistant message (article text)
            assistant_msg = next((m for m in data['messages'] if m['role'] == 'assistant'), None)
            if not assistant_msg:
                continue
                
            raw_text = assistant_msg['content']
            
            cleaned_text = clean_text(raw_text)
            final_text = normalize_structure(cleaned_text)
            
            if final_text:
                assistant_msg['content'] = final_text
                fout.write(json.dumps(data, ensure_ascii=False) + '\n')
                cleaned_count += 1
            else:
                if total_count < 5:
                    wc_raw = len(raw_text.split())
                    wc_clean = len(cleaned_text.split())
                    par_clean = len(cleaned_text.split('\n\n'))
                    print(f"DEBUG: Record {total_count} filtered. RawWC: {wc_raw}, CleanWC: {wc_clean}, CleanPar: {par_clean}")
                
    if cleaned_count > 0:
        os.replace(output_temp, output_final)
    else:
        print("Warning: No records passed cleaning/normalization.")
                
    print(f"Cleaned {cleaned_count}/{total_count} records. Saved to {output_final}.")

if __name__ == "__main__":
    clean_dataset_v2()
