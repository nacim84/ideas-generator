import feedparser
import sqlite3
import json
import os
import time
from datetime import datetime

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

DB_NAME = os.path.join(os.path.dirname(__file__), config['db_name'])

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            published TEXT,
            summary TEXT,
            subreddit TEXT,
            fetched_at TEXT
        )
    ''')
    conn.commit()
    return conn

def collect_feed(subreddit):
    url = f"https://www.reddit.com/r/{subreddit}/.rss"
    print(f"Fetching {url}...")
    # Add User-Agent to avoid 429 Too Many Requests from Reddit
    # feedparser allows passing 'agent' or setting headers via other means if needed, 
    # but 'agent' parameter is the simplest way to set User-Agent in feedparser.
    feed = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    if feed.bozo:
        print(f"  Error parsing feed for {subreddit}: {feed.bozo_exception}")
        return []

    posts = []
    for entry in feed.entries:
        # Reddit RSS IDs are usually unique URLs or IDs
        post_id = entry.id if 'id' in entry else entry.link
        published = entry.published if 'published' in entry else datetime.now().isoformat()
        summary = entry.summary if 'summary' in entry else ""
        
        posts.append((
            post_id,
            entry.title,
            entry.link,
            published,
            summary,
            subreddit,
            datetime.now().isoformat()
        ))
    return posts

def save_posts(conn, posts):
    c = conn.cursor()
    new_count = 0
    for post in posts:
        try:
            c.execute('''
                INSERT INTO posts (id, title, link, published, summary, subreddit, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', post)
            new_count += 1
        except sqlite3.IntegrityError:
            # Already exists
            pass
    conn.commit()
    print(f"  Saved {new_count} new posts.")

def main():
    conn = init_db()
    
    # Extract unique subreddits from all categories
    target_subreddits = set()
    if 'subreddits' in config: # Backward compatibility
        target_subreddits.update(config['subreddits'])
    
    if 'categories' in config:
        for cat_data in config['categories'].values():
            target_subreddits.update(cat_data.get('subreddits', []))

    for sub in target_subreddits:
        posts = collect_feed(sub)
        if posts:
            save_posts(conn, posts)
        # Be nice to Reddit's servers
        time.sleep(2)
    conn.close()
    print("Collection complete.")

if __name__ == "__main__":
    main()
