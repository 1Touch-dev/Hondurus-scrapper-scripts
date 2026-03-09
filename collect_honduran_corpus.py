import os
import json
import logging
from apify_client import ApifyClient
from scrapers.article_scraper import run_article_scrape, download_items, get_criterio_page_function, get_generic_wp_page_function, get_news_page_function
from scrapers.reddit_scraper import run_reddit_scrape
from utils.processor import clean_text, format_gpt_jsonl, format_os_jsonl, format_comment_slang, save_jsonl, anonymize_username, load_existing_data
from utils.reporter import generate_report

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# Output files
GPT_FILE = "dataset_gpt_finetune.jsonl"
OS_FILE = "dataset_open_source.jsonl"
SLANG_FILE = "dataset_comment_slang.jsonl"
REPORT_FILE = "summary_report.md"

import hashlib

def process_articles(source_name, items, user_map, seen_hashes):
    gpt_data = []
    os_data = []
    comment_data = []
    processed_articles = 0
    processed_comments = 0
    
    for item in items:
        raw_text = item.get('text', '')
        text = clean_text(raw_text)
        
        if not text:
            continue
            
        content_hash = hashlib.md5(text.strip().encode('utf-8')).hexdigest()
        if content_hash in seen_hashes:
            continue
            
        author = item.get('author', 'Unknown')
        source = item.get('source', source_name)
        title = item.get('title', 'Untitled')
        
        if len(text) >= 1500:
            gpt_data.append(format_gpt_jsonl(author, source, title, text))
            os_data.append(format_os_jsonl(author, source, title, text))
            processed_articles += 1
            seen_hashes.add(content_hash)
            
        # Process embedded comments
        comments = item.get('comments', [])
        for c in comments:
            c_text = clean_text(c.get('text', ''))
            if c_text:
                comment_data.append(format_comment_slang(source, title, c_text, c.get('date', '')))
                processed_comments += 1
        
    save_jsonl(gpt_data, GPT_FILE)
    save_jsonl(os_data, OS_FILE)
    save_jsonl(comment_data, SLANG_FILE)
    return processed_articles, processed_comments

def process_reddit_items(items, user_map, seen_hashes):
    slang_data = []
    processed_count = 0
    
    for item in items:
        comment_text = clean_text(item.get('body', item.get('comment_text', '')))
        if not comment_text and item.get('selftext'):
            comment_text = clean_text(item.get('selftext'))
            
        if not comment_text:
            continue
            
        content_hash = hashlib.md5(comment_text.strip().encode('utf-8')).hexdigest()
        if content_hash in seen_hashes:
            continue
            
        author = item.get('username', item.get('author', item.get('user_id', 'Unknown')))
        anon_id = anonymize_username(author, user_map)
        
        date = item.get('createdAt', item.get('date', ''))
        thread_title = item.get('postTitle', item.get('thread_title', item.get('title', 'Unknown Thread')))
        
        slang_data.append(format_comment_slang("reddit", thread_title, comment_text, date))
        processed_count += 1
        seen_hashes.add(content_hash)
        
    save_jsonl(slang_data, SLANG_FILE)
    return processed_count

def run_pipeline(target_articles=300, target_comments=2000):
    logger.info("Starting Honduran Corpus Expansion Pipeline")
    
    # Load existing data for deduplication
    seen_article_hashes = load_existing_data(GPT_FILE)
    seen_slang_hashes = load_existing_data(SLANG_FILE)
    
    logger.info(f"Loaded {len(seen_article_hashes)} existing articles and {len(seen_slang_hashes)} existing comments/hashes")
    
    results_summary = {
        "Existing Articles": len(seen_article_hashes),
        "Existing Comments": len(seen_slang_hashes)
    }
    user_map = {} 

    # Phase 1: Article Expansion
    authors_extra = ["jorge", "emy", "katerin-galo", "francia-guardiola", "marcia-perdomo", "julio-raudales", "hugo-noe-pino", "thelma-mejia", "pablo-zelaya", "claudia-mendoza"]
    
    expansion_sources = {
        "Radios_HN": {
            "urls": [
                "https://www.radioamerica.hn/category/nacionales/",
                "https://www.radioamerica.hn/category/noticias/"
            ],
            "fn": get_news_page_function("radioamerica.hn"),
            "max": 500
        },
        "Diez_Sports": {
            "urls": ["https://www.diez.hn/fútbol-hondureño", "https://www.diez.hn/internacional"],
            "fn": get_news_page_function("diez.hn"),
            "max": 500
        },
        "WordPress_Blogs": {
            "urls": [
                "https://rodriguezhn.wordpress.com/category/articulos/",
                "https://504honduras.blogspot.com/",
                "https://socialhonduras.wordpress.com/",
                "https://portalcatracho.wordpress.com/",
                "https://marienzara.wordpress.com/",
                "https://deulloa1971.wordpress.com/"
            ],
            "fn": get_generic_wp_page_function("blogs"),
            "max": 1000
        }
    }

    current_articles = len(seen_article_hashes)
    current_comments = len(seen_slang_hashes)

    for name, config in expansion_sources.items():
        if current_articles >= target_articles:
            logger.info(f"Target of {target_articles} articles reached. Skipping {name}")
            continue
            
        try:
            dataset_id = run_article_scrape(client, name, config['urls'], config['fn'], max_requests=config['max'])
            items = download_items(client, dataset_id)
            art_count, com_count = process_articles(name, items, user_map, seen_article_hashes)
            results_summary[f"{name} (Added Articles)"] = art_count
            current_articles += art_count
            current_comments += com_count
            logger.info(f"Processed {art_count} new articles. Total: {current_articles}/{target_articles}")
        except Exception as e:
            logger.error(f"Error processing {name}: {str(e)}")

    # Phase 2: Reddit Expansion
    reddit_keywords = [
        "hondureñismos", "caliche", "maje", "cipote", "pijeado", "no hay clavo", 
        "Honduras", "Tegucigalpa", "San Pedro Sula", "Catracho", "Gringo en Honduras",
        "Modismos", "Slang", "Hondureño", "Comida Hondureña", "Politica Honduras"
    ]
    
    sorts = ["new", "hot", "top"]
    for sort in sorts:
        if current_comments >= target_comments:
            break
            
        try:
            dataset_id = run_reddit_scrape(client, "Honduras", reddit_keywords, max_items=1000, sort=sort)
            items = download_items(client, dataset_id)
            count = process_reddit_items(items, user_map, seen_slang_hashes)
            results_summary[f"Reddit_{sort} (Added)"] = count
            current_comments += count
            logger.info(f"Processed {count} new Reddit items via {sort}. Total: {current_comments}/{target_comments}")
        except Exception as e:
            logger.error(f"Error processing Reddit {sort}: {str(e)}")

    # Generate Report
    generate_report(results_summary, REPORT_FILE)
    logger.info(f"Expansion Pipeline Complete. Total Articles: {current_articles}, Total Comments: {current_comments}")
    logger.info(f"Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    run_pipeline(target_articles=300, target_comments=2000)
