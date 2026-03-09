import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (API Key)
load_dotenv(os.path.join(os.getcwd(), 'project', '.env'))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use the newly trained v2 model
MODEL_ID = "ft:gpt-4o-mini-2024-07-18:1touch:honduras-news-v2:DHQyNyzt"

def generate_article(topic, domain="political_investigation", outlet="criterio.hn"):
    print(f"🚀 Generating '{domain}' article about: {topic}...\n")
    
    system_prompt = f"[COUNTRY=Honduras]\n[DOMAIN={domain}]\n[OUTLET={outlet}]\n[TASK=article_generation]"
    user_prompt = f"Escribe un artículo detallado sobre {topic} en el estilo editorial de {outlet}."
    
    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        print("--- GENERATED ARTICLE ---\n")
        print(content)
        print("\n--- END ---")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Default test topic
    topic = "la situación actual de la transparencia en el sistema judicial hondureño"
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    
    generate_article(topic)
