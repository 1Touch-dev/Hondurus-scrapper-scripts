import re
import json
import os
import hashlib
from datetime import datetime

def clean_text(text):
    if not text:
        return ""
    # Remove HTML tags (basic approach)
    text = re.sub(r'<[^>]+>', '', text)
    # Remove common navigation/junk text patterns
    junk_patterns = [
        r'(?i)Read more', r'(?i)Share this:', r'(?i)Facebook', r'(?i)Twitter', 
        r'(?i)WhatsApp', r'(?i)Instagram', r'(?i)Pinterest', r'(?i)LinkedIn', 
        r'(?i)Subscribe', r'(?i)Related Articles', r'(?i)Privacy Policy', 
        r'(?i)Terms of Service'
    ]
    for pattern in junk_patterns:
        text = re.sub(pattern, '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def anonymize_username(username, user_map):
    if not username:
        return "user_anonymous"
    if username not in user_map:
        user_map[username] = f"user_{len(user_map) + 1:03d}"
    return user_map[username]

def get_system_and_instruction(source, author):
    src = source.lower()
    
    if 'criterio.hn' in src:
        domain = "political_investigation"
        desc = "political investigative journalism"
    elif 'laprensa' in src or 'elheraldo' in src:
        domain = "mainstream_news"
        desc = "mainstream news coverage"
    elif 'diez' in src:
        domain = "sports_coverage"
        desc = "sports coverage"
    elif 'radio' in src:
        domain = "radio_broadcast"
        desc = "a radio news broadcast"
    else:
        domain = "cultural_blog"
        desc = "a cultural blog post"
        
    tags = f"[COUNTRY=Honduras]\n[DOMAIN={domain}]\n[OUTLET={source}]"
    
    if author and author.strip() and author != "Unknown":
        author_clean = author.replace(' ', '_').lower()
        tags += f"\n[AUTHOR={author_clean}]"
        instruction = f"Write {desc} in the style of {author}."
    else:
        instruction = f"Write {desc} in the editorial voice of {source}."
        
    tags += "\n[TASK=article_generation]"
        
    return tags, instruction

def format_gpt_jsonl(author, source, title, text):
    tags, instruction = get_system_and_instruction(source, author)
    return {
        "messages": [
            {"role": "system", "content": tags},
            {"role": "user", "content": f"{instruction} Write an article about: {title}"},
            {"role": "assistant", "content": text}
        ]
    }

def format_os_jsonl(author, source, title, text):
    tags, instruction = get_system_and_instruction(source, author)
    return {
        "instruction": f"{tags}\n\n{instruction} Write an article about: {title}",
        "output": text
    }

def format_comment_slang(source, thread_title, comment_text, date):
    return {
        "source": source,
        "thread_title": thread_title,
        "comment_text": comment_text,
        "date": date
    }

def save_jsonl(data, filepath):
    with open(filepath, 'a', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def load_existing_data(filepath):
    """
    Loads existing data from a JSONL file and returns a set of content MD5 hashes.
    We use MD5 of the main text content for deduplication since URLs aren't stored in all formats.
    """
    seen_hashes = set()
    if not os.path.exists(filepath):
        return seen_hashes
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                content = ""
                if 'messages' in item: # GPT format
                    content = item['messages'][-1]['content']
                elif 'instruction' in item: # OS format
                    content = item['output']
                elif 'comment_text' in item: # Slang format
                    content = item['comment_text']
                
                if content:
                    # Clean slightly before hashing to be more robust
                    clean_content = content.strip()
                    md5_hash = hashlib.md5(clean_content.encode('utf-8')).hexdigest()
                    seen_hashes.add(md5_hash)
            except Exception as e:
                continue
    return seen_hashes
