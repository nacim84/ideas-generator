import os
import sqlite3
import json
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from the root .env
# Structure is execution/reddit_analyzer/analyze_ideas.py -> .env is two levels up
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

DB_NAME = os.path.join(os.path.dirname(__file__), config['db_name'])

import time
from google.api_core import exceptions

def get_recent_posts(hours=24, limit=20):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Calculate cutoff time
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    # Select posts fetched recently
    query = '''
        SELECT title, summary, subreddit, link 
        FROM posts 
        WHERE fetched_at > ? 
        ORDER BY fetched_at DESC 
        LIMIT ?
    '''
    c.execute(query, (cutoff, limit))
    posts = c.fetchall()
    conn.close()
    return posts

def analyze_posts(posts):
    if not posts:
        return "No recent posts found to analyze."

    # Construct Prompt
    posts_text = ""
    for p in posts:
        title, summary, sub, link = p
        # Limit summary length further to save tokens
        posts_text += f"- [{sub}] {title}\n  Summary: {summary[:150]}...\n  Link: {link}\n\n"

    prompt = f"""
    Tu es un analyste commercial expert. Analyse les publications Reddit suivantes provenant de communautés liées au business.
    Identifie 5 idées de business prometteuses, tendances ou problèmes ("pain points") que des entrepreneurs pourraient résoudre.
    
    Formate ta réponse sous forme de rapport Markdown en FRANÇAIS. 
    IMPORTANT : N'utilise PAS de tableau pour les idées. Utilise le format suivant pour une lisibilité maximale :

    # Rapport d'Idées Business

    ## 📊 Résumé Exécutif
    Un aperçu de 2 phrases sur le sentiment actuel du marché.

    ## 🚀 Top 5 Opportunités

    ### 1. [Nom de l'Idée/Tendance]
    **🧐 Le Problème / Insight :**
    [Description du problème. Cite le contexte spécifique du post reddit ici]

    **💡 Solution / Produit Proposé :**
    [Description concrète de la solution]

    ---
    (Répète pour les idées 2 à 5)
    
    Voici les données à analyser :
    {posts_text}
    """

    model = genai.GenerativeModel('gemini-flash-latest')
    
    # Simple retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except exceptions.ResourceExhausted as e:
            print(f"Quota exceeded (attempt {attempt+1}/{max_retries}). Retrying in 20 seconds...")
            time.sleep(20)
        except Exception as e:
            print(f"An error occurred: {e}")
            return f"Analysis failed due to error: {e}"
            
    return "Analysis failed after retries due to quota limits."

def main():
    print("Fetching recent posts...")
    posts = get_recent_posts(hours=24)
    print(f"Found {len(posts)} posts. Analyzing with Gemini...")
    
    analysis = analyze_posts(posts)
    
    print("\n--- ANALYSIS REPORT ---\n")
    print(analysis)
    
    # Save to a temporary file for the next step (emailing)
    output_path = os.path.join(os.path.dirname(__file__), 'latest_analysis.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(analysis)
    print(f"\nAnalysis saved to {output_path}")

if __name__ == "__main__":
    main()
