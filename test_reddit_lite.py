from apify_client import ApifyClient
from scrapers.reddit_scraper import run_reddit_scrape
from utils.processor import clean_text, format_comment_slang, save_jsonl, anonymize_username
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

def test_reddit():
    reddit_keywords = ["hondureñismos", "maje", "cipote"]
    user_map = {}
    SLANG_FILE = "test_reddit_slang.jsonl"
    
    try:
        dataset_id = run_reddit_scrape(client, "Honduras", reddit_keywords, max_items=10)
        items = []
        dataset_client = client.dataset(dataset_id)
        for item in dataset_client.iterate_items():
            items.append(item)
            
        print(f"Items found: {len(items)}")
        if items:
            print(f"Sample item: {items[0].get('body', 'No body')[:100]}")
            
    except Exception as e:
        print(f"Reddit test failed: {e}")

if __name__ == "__main__":
    test_reddit()
