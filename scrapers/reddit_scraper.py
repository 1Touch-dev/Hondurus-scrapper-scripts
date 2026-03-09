def run_reddit_scrape(client, subreddit, keywords, max_items=1000, sort="new"):
    # trudax/reddit-scraper-lite uses 'searches' and 'type'
    run_input = {
        "searches": keywords,
        "searchCommunityName": subreddit,
        "type": "post",
        "sort": sort,
        "time": "all",
        "maxItems": max_items,
        "maxComments": 100, # Increased for more depth
        "proxy": {"useApifyProxy": True}
    }
    
    print(f"Starting Reddit Scraper Lite for keywords in r/{subreddit} (Sort: {sort})...")
    run = client.actor("trudax/reddit-scraper-lite").call(run_input=run_input)
    print(f"Reddit scrape completed. Dataset ID: {run['defaultDatasetId']}")
    return run['defaultDatasetId']
