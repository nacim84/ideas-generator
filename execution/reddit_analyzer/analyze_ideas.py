import argparse
import json
import os
import sqlite3
from datetime import datetime, timedelta

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from the root .env
dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
)
load_dotenv(dotenv_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not found in .env")
    exit(1)

GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-3-flash-preview")

genai.configure(api_key=GOOGLE_API_KEY)

# Config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

DB_NAME = os.path.join(os.path.dirname(__file__), config["db_name"])

import time

from google.api_core import exceptions


def get_recent_posts(hours=24, limit=20, category=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Calculate cutoff time
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

    # Define subreddits filter
    target_subreddits = []
    if category:
        if "subreddits" in config:
            target_subreddits = [
                s["name"]
                for s in config["subreddits"]
                if isinstance(s, dict) and s.get("category") == category
            ]

        if not target_subreddits:
            print(f"Warning: No subreddits found for category '{category}'.")
            return []

    query = "SELECT title, summary, subreddit, link FROM posts WHERE fetched_at > ?"
    params = [cutoff]

    if target_subreddits:
        placeholders = ",".join("?" for _ in target_subreddits)
        query += f" AND subreddit IN ({placeholders})"
        params.extend(target_subreddits)

    query += " ORDER BY fetched_at DESC LIMIT ?"
    params.append(limit)

    c.execute(query, tuple(params))
    posts = c.fetchall()
    conn.close()
    return posts


def analyze_posts(posts, category_name="Général"):
    if not posts:
        return f"Aucun post récent trouvé pour la catégorie {category_name}."

    # Construct Prompt
    posts_text = ""
    for p in posts:
        title, summary, sub, link = p
        # Limit summary length further to save tokens
        posts_text += (
            f"- [{sub}] {title}\n  Summary: {summary[:150]}...\n  Link: {link}\n\n"
        )

    prompt = f"""
    Tu es un analyste commercial expert. Analyse les publications Reddit suivantes provenant de la catégorie '{category_name}'.
    Identifie 5 idées de business prometteuses, tendances ou problèmes ("pain points") que des entrepreneurs pourraient résoudre.

    Formate ta réponse sous forme de rapport Markdown en FRANÇAIS.
    IMPORTANT : N'utilise PAS de tableau pour les idées. Utilise le format suivant pour une lisibilité maximale :

    # Rapport d'Idées Business : {category_name}

    ## 📊 Résumé Exécutif
    Un aperçu de 2 phrases sur le sentiment actuel dans cette niche.

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

    model = genai.GenerativeModel(GOOGLE_MODEL)

    # Simple retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except exceptions.ResourceExhausted as e:
            print(
                f"Quota exceeded (attempt {attempt + 1}/{max_retries}). Retrying in 20 seconds..."
            )
            time.sleep(20)
        except Exception as e:
            print(f"An error occurred: {e}")
            return f"Analysis failed due to error: {e}"

    return "Analysis failed after retries due to quota limits."


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Reddit posts for business ideas."
    )
    parser.add_argument(
        "--category", type=str, help="Category name from config.json to analyze"
    )
    args = parser.parse_args()

    print(
        f"Fetching recent posts for category: {args.category if args.category else 'ALL'}..."
    )
    posts = get_recent_posts(hours=24, category=args.category)
    print(f"Found {len(posts)} posts. Analyzing with Gemini...")

    cat_display_name = args.category if args.category else "Business Général"
    analysis = analyze_posts(posts, category_name=cat_display_name)

    print("\n--- ANALYSIS REPORT ---\n")
    print(analysis)

    # Save to a temporary file specific to the category
    filename = (
        f"latest_analysis_{args.category}.md" if args.category else "latest_analysis.md"
    )
    output_path = os.path.join(os.path.dirname(__file__), filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(analysis)
    print(f"\nAnalysis saved to {output_path}")


if __name__ == "__main__":
    main()
