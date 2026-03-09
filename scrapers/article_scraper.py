from apify_client import ApifyClient
import time

def get_generic_wp_page_function(source_domain):
    return f"""
    async function pageFunction(context) {{
        const {{ request, log, jQuery }} = context;
        const $ = jQuery;

        const safeEnqueue = async (selector, label) => {{
            const links = [];
            $(selector).each(function() {{
                const href = $(this).attr('href');
                if (href) links.push(href);
            }});
            
            for (const url of links) {{
                try {{
                    const absoluteUrl = new URL(url, request.url).href;
                    if (context.enqueueLinks) {{
                        await context.enqueueLinks({{ urls: [absoluteUrl], userData: {{ label }} }});
                    }} else if (context.enqueueRequest) {{
                        await context.enqueueRequest({{ url: absoluteUrl, userData: {{ label }} }});
                    }}
                }} catch (e) {{
                    log.error('Failed to enqueue URL: ' + url + ' error: ' + e.message);
                }}
            }}
        }};

        if (request.userData.label === 'DETAIL') {{
            const title = $('.entry-title, .post-title, h1').first().text().trim();
            const author = $('.entry-author, .author-name, .vcard').text().trim() || 'Unknown';
            const date = $('time, .entry-date, .post-date').first().attr('datetime') || $('.entry-date').text().trim();
            const text = $('.entry-content, .post-content, article').text().trim();
            const url = request.url;

            if (text.length < 1500) {{
                log.info(`Skipping article ${{url}} due to short text length (${{text.length}} chars)`);
                return null;
            }}

            return {{
                source: '{source_domain}',
                author,
                title,
                date,
                url,
                text
            }};
        }} else {{
            // Enqueue article links
            await safeEnqueue('a[rel="bookmark"], .entry-title a, h2 a', 'DETAIL');
            
            // Handle pagination (WordPress style)
            await safeEnqueue('.next, .older-posts, .nav-previous a, a.page-numbers.next', 'LIST');
        }}
    }}
    """

def get_criterio_page_function():
    return """
    async function pageFunction(context) {
        const { request, log, jQuery } = context;
        const $ = jQuery;

        const safeEnqueue = async (selector, label) => {
            const links = [];
            $(selector).each(function() {
                const href = $(this).attr('href');
                if (href) links.push(href);
            });
            
            for (const url of links) {
                try {
                    const absoluteUrl = new URL(url, request.url).href;
                    if (context.enqueueLinks) {
                        await context.enqueueLinks({ urls: [absoluteUrl], userData: { label } });
                    } else if (context.enqueueRequest) {
                        await context.enqueueRequest({ url: absoluteUrl, userData: { label } });
                    }
                } catch (e) {
                    log.error('Failed to enqueue URL: ' + url + ' error: ' + e.message);
                }
            }
        };

        if (request.userData.label === 'DETAIL') {
            const title = $('h1.elementor-heading-title').text().trim();
            const author = $('.elementor-post-info__item--type-author .elementor-post-info__item-name').text().trim() || 'Unknown';
            const date = $('.elementor-post-info__item--type-date .elementor-post-info__item-date').text().trim();
            const text = $('.elementor-widget-theme-post-content').text().trim();
            const url = request.url;

            // Extract comments
            const comments = [];
            $('#comments li.comment').each(function() {
                const commentText = $(this).find('.comment-content, .comment-body').text().trim();
                const commentAuthor = $(this).find('.comment-author, .fn').text().trim();
                const commentDate = $(this).find('time').attr('datetime') || $(this).find('.comment-metadata time').text().trim();
                if (commentText) {
                    comments.push({ text: commentText, author: commentAuthor, date: commentDate });
                }
            });

            if (text.length < 1500 && comments.length === 0) {
                log.info(`Skipping article ${url} due to short text length and no comments`);
                return null;
            }

            return {
                source: 'criterio.hn',
                author,
                title,
                date,
                url,
                text,
                comments
            };
        } else {
            // Enqueue links from author pages
            await safeEnqueue('.elementor-post__title a', 'DETAIL');
            
            // Handle pagination
            await safeEnqueue('.next.page-numbers', 'LIST');
        }
    }
    """

def get_news_page_function(source_domain):
    return f"""
    async function pageFunction(context) {{
        const {{ request, log, jQuery }} = context;
        const $ = jQuery;

        const safeEnqueue = async (selector, label) => {{
            const links = [];
            $(selector).each(function() {{
                const href = $(this).attr('href');
                if (href) links.push(href);
            }});
            
            for (const url of links) {{
                try {{
                    const absoluteUrl = new URL(url, request.url).href;
                    if (context.enqueueLinks) {{
                        await context.enqueueLinks({{ urls: [absoluteUrl], userData: {{ label }} }});
                    }} else if (context.enqueueRequest) {{
                        await context.enqueueRequest({{ url: absoluteUrl, userData: {{ label }} }});
                    }}
                }} catch (e) {{
                    log.error('Failed to enqueue URL: ' + url + ' error: ' + e.message);
                }}
            }}
        }};

        if (request.userData.label === 'DETAIL') {{
            const title = $('h1.headline, h1.article-title, h1.entry-title, .post-title, h1').first().text().trim();
            const author = $('.article-author, .author, .entry-author, .vcard').text().trim() || 'Unknown';
            const date = $('.article-date, time, .entry-date, .post-date').first().text().trim();
            const text = $('.article-body, .entry-content, .post-content, div.paragraph, .td-post-content, article').text().trim();
            const url = request.url;

            if (text.length < 1500) {{
                log.info(`Skipping article ${{url}} due to short text length (${{text.length}} chars)`);
                return null;
            }}

            return {{
                source: '{source_domain}',
                author,
                title,
                date,
                url,
                text
            }};
        }} else {{
            // Article links
            await safeEnqueue('a:has(h2), .story-card a, .article-link, h2 a, .entry-title a', 'DETAIL');
            
            // Pagination
            await safeEnqueue('.next, .older-posts, .nav-previous a, a.page-numbers.next, .td-next-page a', 'LIST');
        }}
    }}
    """

def run_article_scrape(client, source_name, start_urls, page_function, max_requests=1000):
    run_input = {
        "startUrls": [{"url": url, "userData": {"label": "LIST"}} for url in start_urls],
        "pageFunction": page_function,
        "maxRequestsPerCrawl": max_requests,
        "maxConcurrency": 10,
        "proxyConfiguration": {"useApifyProxy": True},
        "waitUntil": ["networkidle2"]
    }
    
    print(f"Starting scrape for {source_name}...")
    run = client.actor("apify/web-scraper").call(run_input=run_input)
    print(f"Scrape for {source_name} completed. Dataset ID: {run['defaultDatasetId']}")
    return run['defaultDatasetId']

def download_items(client, dataset_id):
    items = []
    dataset_client = client.dataset(dataset_id)
    offset = 0
    limit = 1000
    while True:
        resp = dataset_client.list_items(offset=offset, limit=limit)
        batch = resp.items
        if not batch:
            break
        items.extend(batch)
        offset += limit
    return items
