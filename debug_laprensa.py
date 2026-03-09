from apify_client import ApifyClient
import json
import os

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
dataset_id = "S9huyVHogthbcsEr1" # This is the run ID, but dataset ID is usually defaultDatasetId

# Get run details
run = client.run(dataset_id).get()
ds_id = run['defaultDatasetId']

items = client.dataset(ds_id).list_items().items
print(f"Total items in dataset: {len(items)}")

for i, item in enumerate(items[:5]):
    print(f"Item {i}:")
    print(f"  Title: {item.get('title')}")
    print(f"  Text Length: {len(item.get('text', ''))}")
    print(f"  URL: {item.get('url')}")
