import sqlite3
import json
import os
import argparse

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

DB_NAME = os.path.join(os.path.dirname(__file__), config['db_name'])

def search(query):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Simple case-insensitive search
    # %query%
    sql_query = f"%{query}%"
    
    c.execute('''
        SELECT title, link, subreddit, published 
        FROM posts 
        WHERE title LIKE ? OR summary LIKE ?
        ORDER BY published DESC
    ''', (sql_query, sql_query))
    
    results = c.fetchall()
    conn.close()
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Search collected Reddit posts.')
    parser.add_argument('query', type=str, help='The search term')
    args = parser.parse_args()
    
    print(f"Searching for '{args.query}' in {DB_NAME}...\n")
    
    results = search(args.query)
    
    if not results:
        print("No results found.")
    else:
        print(f"Found {len(results)} results:\n")
        for row in results:
            title, link, subreddit, published = row
            print(f"[{subreddit}] {title}")
            print(f"Date: {published}")
            print(f"Link: {link}")
            print("-" * 40)

if __name__ == "__main__":
    main()
