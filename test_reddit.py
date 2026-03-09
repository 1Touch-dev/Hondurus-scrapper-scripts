from apify_client import ApifyClient
import os

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

actors_to_test = [
    "trudax/reddit-scraper", # test if limit reset
    "mstephen190/reddit-scraper",
    "epctex/reddit-scraper",
    "maxscraper/reddit-scraper"
]

for actor in actors_to_test:
    print(f"Testing {actor}...")
    run_input = {
        "searchTerms": ["caliche"],
        "searchSubreddits": ["Honduras"],
        "maxItems": 10
    }
    try:
        run = client.actor(actor).call(run_input=run_input)
        print(f"Success! {actor} worked. Dataset ID: {run['defaultDatasetId']}")
        break
    except Exception as e:
        print(f"Failed {actor}: {e}")
