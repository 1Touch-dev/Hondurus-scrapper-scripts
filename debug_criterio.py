from apify_client import ApifyClient
import json
import os

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
client = ApifyClient(APIFY_API_TOKEN)
dataset_id = "fgfLVW3pZyu14NlYx"

items = client.dataset(dataset_id).list_items().items
print(f"Total items in dataset: {len(items)}")

for i, item in enumerate(items[:5]):
    print(f"Item {i}:")
    print(f"  Title: {item.get('title')}")
    print(f"  Text Length: {len(item.get('text', ''))}")
    print(f"  URL: {item.get('url')}")
