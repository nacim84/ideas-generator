import asyncio
from typing import TypedDict, List
import feedparser
import sqlite3
import json
import os
import re
from pathlib import Path
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import google.generativeai as genai
import nltk
from openai import OpenAI
from pydub import AudioSegment
from pydub.effects import normalize
from dotenv import load_dotenv
from google.api_core import exceptions
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import markdown
from langgraph.graph import StateGraph, END

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# Models
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-3-flash-preview")

# Email Configuration (SMTP)
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
SENDER_EMAIL = os.getenv("SMTP_USERNAME") or os.getenv("SENDER_EMAIL", RECIPIENT_EMAIL)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Google Drive Configuration
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
GOOGLE_SERVICE_ACCOUNT_PATH = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_PATH",
    os.path.join(ROOT_DIR, "execution/reddit_analyzer/secrets/service_account.json"),
)
GOOGLE_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
GOOGLE_DRIVE_PARENT_FOLDER_ID = os.getenv(
    "GOOGLE_DRIVE_PARENT_FOLDER_ID", "1mYgr0YXeF71rjoxLsHTLEC5LL67Nbf48"
)
# User email for domain-wide delegation (required for Drive uploads)
GOOGLE_DRIVE_USER_EMAIL = os.getenv("GOOGLE_DRIVE_USER_EMAIL")


class AppState(TypedDict):
    db_path: str
    config: dict
    categories: List[str]
    current_category: str
    analysis_report_path: str
    podcast_script_path: str
    segmented_script_path: str
    raw_audio_dir: str
    final_episode_path: str
    branch_results: List[str]


# --- HELPER FUNCTIONS ---


def send_email_smtp(subject: str, html_content: str, recipient: str) -> bool:
    """Send email using SMTP with Gmail App Password."""
    if not SMTP_PASSWORD:
        print("Warning: SMTP_PASSWORD not set, skipping email.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient, msg.as_string())

    return True


# --- GOOGLE DRIVE HELPER FUNCTIONS ---


def get_drive_service():
    """
    Get Google Drive service.
    - Uses OAuth token (drive_token.json) for personal Gmail accounts
    - Falls back to service account for Workspace with domain-wide delegation
    """
    token_path = os.path.join(os.path.dirname(__file__), "secrets", "drive_token.json")
    credentials_path = os.path.join(
        os.path.dirname(__file__), "secrets", "drive_credentials.json"
    )

    # Try OAuth 2.0 first (for personal Gmail accounts)
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, GOOGLE_DRIVE_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        return build("drive", "v3", credentials=creds)

    # Try OAuth flow if credentials.json exists (first-time setup)
    if os.path.exists(credentials_path):
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path, GOOGLE_DRIVE_SCOPES
        )
        creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        return build("drive", "v3", credentials=creds)

    # Fall back to service account (for Workspace with domain-wide delegation)
    if os.path.exists(GOOGLE_SERVICE_ACCOUNT_PATH):
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_PATH, scopes=GOOGLE_DRIVE_SCOPES
        )
        if GOOGLE_DRIVE_USER_EMAIL:
            credentials = credentials.with_subject(GOOGLE_DRIVE_USER_EMAIL)
        return build("drive", "v3", credentials=credentials)

    print("Warning: No Google Drive credentials found.")
    return None


def get_or_create_drive_folder(service, folder_name: str, parent_id: str) -> str:
    """Get existing folder or create new one in Google Drive."""
    # Search for existing folder
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    # Create new folder
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    print(f"Created Drive folder: {folder_name}")
    return folder.get("id")


def upload_to_drive(
    service, local_path: str, folder_id: str, mime_type: str = None
) -> str:
    """Upload a file to Google Drive folder."""
    if not os.path.exists(local_path):
        print(f"Warning: File not found: {local_path}")
        return None

    filename = os.path.basename(local_path)

    # Auto-detect mime type
    if mime_type is None:
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".json": "application/json",
            ".md": "text/markdown",
            ".txt": "text/plain",
        }
        mime_type = mime_types.get(ext, "application/octet-stream")

    file_metadata = {"name": filename, "parents": [folder_id]}

    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )

    print(f"Uploaded to Drive: {filename} -> {file.get('webViewLink')}")
    return file.get("id")


def setup_drive_folders(service, category: str) -> dict:
    """Create folder structure for a category in Google Drive."""
    # Create date folder (e.g., "2026-01-25")
    date_folder_name = datetime.now().strftime("%Y-%m-%d")
    date_folder_id = get_or_create_drive_folder(
        service, date_folder_name, GOOGLE_DRIVE_PARENT_FOLDER_ID
    )

    # Create category folder
    category_folder_id = get_or_create_drive_folder(service, category, date_folder_id)

    # Create subfolders
    folders = {
        "reports": get_or_create_drive_folder(service, "reports", category_folder_id),
        "scripts": get_or_create_drive_folder(service, "scripts", category_folder_id),
        "segments": get_or_create_drive_folder(service, "segments", category_folder_id),
        "episodes": get_or_create_drive_folder(service, "episodes", category_folder_id),
    }

    return folders


# Helper functions for analyze_ideas_node
def get_recent_posts_for_analysis(
    db_path: str, config: dict, hours=24, limit=20, category=None
):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

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
    placeholders = ",".join("?" for _ in target_subreddits)
    query += f" AND subreddit IN ({placeholders})"
    params.extend(target_subreddits)
    query += " ORDER BY fetched_at DESC LIMIT ?"
    params.append(limit)

    c.execute(query, tuple(params))
    posts = c.fetchall()
    conn.close()
    return posts


def run_analysis(posts, category_name="Général"):
    if not posts:
        return f"Aucun post récent trouvé pour la catégorie {category_name}."

    posts_text = ""
    for p in posts:
        title, summary, sub, link = p
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


# --- GRAPH NODES ---
def collect_data_node(state: AppState) -> dict:
    """
    Initializes the database, collects posts from Reddit feeds, and saves them.
    Returns a dictionary with the categories to be processed.
    """
    print("---COLLECTING DATA---")
    db_path = state["db_path"]
    config = state["config"]

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            published TEXT,
            summary TEXT,
            subreddit TEXT,
            fetched_at TEXT
        )
    """)
    conn.commit()

    target_subreddits = {
        sub_entry.get("name")
        for sub_entry in config.get("subreddits", [])
        if isinstance(sub_entry, dict)
    }

    for sub in target_subreddits:
        if not sub:
            continue
        url = f"https://www.reddit.com/r/{sub}/.rss"
        print(f"Fetching {url}...")
        feed = feedparser.parse(
            url,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        )

        if feed.bozo:
            print(f"  Error parsing feed for {sub}: {feed.bozo_exception}")
            continue

        posts_to_save = []
        for entry in feed.entries:
            post_id = entry.id if "id" in entry else entry.link
            published = (
                entry.published if "published" in entry else datetime.now().isoformat()
            )
            summary = entry.summary if "summary" in entry else ""
            posts_to_save.append(
                (
                    post_id,
                    entry.title,
                    entry.link,
                    published,
                    summary,
                    sub,
                    datetime.now().isoformat(),
                )
            )

        if posts_to_save:
            c = conn.cursor()
            new_count = 0
            for post in posts_to_save:
                try:
                    c.execute(
                        """
                        INSERT INTO posts (id, title, link, published, summary, subreddit, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        post,
                    )
                    new_count += 1
                except sqlite3.IntegrityError:
                    pass  # Already exists
            conn.commit()
            print(f"  Saved {new_count} new posts for {sub}.")

        time.sleep(2)

    conn.close()

    categories = list(set(sub["category"] for sub in config.get("subreddits", [])))
    print(f"---DATA COLLECTION COMPLETE---")
    return {"categories": categories, "branch_results": []}


def analyze_ideas_node(state: AppState) -> dict:
    """
    Analyzes recent posts for a given category and saves the report.
    """
    category = state["current_category"]
    print(f"---ANALYZING IDEAS FOR CATEGORY: {category}---")

    posts = get_recent_posts_for_analysis(
        state["db_path"], state["config"], category=category
    )
    print(f"Found {len(posts)} posts for '{category}'. Analyzing with Gemini...")

    analysis = run_analysis(posts, category_name=category)

    # Save report and update state
    report_filename = f"latest_analysis_{category}.md"
    report_path = os.path.join(os.path.dirname(__file__), report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(analysis)

    print(f"---ANALYSIS FOR {category} COMPLETE---")
    return {"analysis_report_path": report_path}


def send_email_node(state: AppState) -> dict:
    """
    Sends the analysis report via email using SMTP.
    """
    category = state["current_category"]
    report_path = state["analysis_report_path"]
    print(f"---SENDING EMAIL FOR CATEGORY: {category}---")

    if not RECIPIENT_EMAIL:
        print("Warning: RECIPIENT_EMAIL not set, skipping email.")
        return {}
    if not os.path.exists(report_path):
        print(f"Warning: Report file {report_path} not found, skipping email.")
        return {}

    with open(report_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content)
    current_date = datetime.now().strftime("%d/%m/%Y")
    subject = f"[{category}] Idées Business Du Jour : {current_date}"

    try:
        if send_email_smtp(subject, html_content, RECIPIENT_EMAIL):
            print(f"---EMAIL FOR {category} SENT SUCCESSFULLY---")
    except Exception as e:
        print(f"An error occurred while sending email: {e}")

    return {}


def generate_podcast_script_node(state: AppState) -> dict:
    """
    Generates a podcast script from the analysis report.
    """
    category = state["current_category"]
    report_path = state["analysis_report_path"]
    print(f"---GENERATING PODCAST SCRIPT FOR CATEGORY: {category}---")

    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Analysis report not found at {report_path}")

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    config_path = Path(__file__).parent / "podcast_config_advanced.json"
    with open(config_path, "r", encoding="utf-8") as f:
        podcast_config = json.load(f)

    # Simple parsing of the markdown report
    lines = content.split("\n")
    segments = []
    current_speaker = "HOST"
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        if stripped_line.startswith("## 🚀"):
            current_speaker = "HOST"
        elif stripped_line.startswith("###"):
            current_speaker = "EXPERT"

        # Normalize text for TTS
        normalization_rules = podcast_config["content_strategy"]["text_normalization"]
        normalized_line = stripped_line
        for original, normalized in normalization_rules.items():
            normalized_line = re.compile(
                r"\b" + re.escape(original) + r"\b", re.IGNORECASE
            ).sub(normalized, normalized_line)

        segments.append({"speaker": current_speaker, "content": normalized_line})

    podcast_data = {
        "title": f"Idées Business du {datetime.now().strftime('%d %B %Y')} - {category}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "segments": segments,
    }

    output_dir = Path(__file__).parent / "scripts"
    output_dir.mkdir(exist_ok=True)
    output_file = (
        output_dir
        / f"podcast_script_{category}_{datetime.now().strftime('%Y%m%d')}.json"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(podcast_data, f, ensure_ascii=False, indent=2)

    print(f"---PODCAST SCRIPT FOR {category} GENERATED: {output_file}---")
    return {"podcast_script_path": str(output_file)}


def semantic_segmentation_node(state: AppState) -> dict:
    """
    Applies semantic segmentation to the podcast script.
    """
    script_path = state["podcast_script_path"]
    category = state["current_category"]
    print(f"---SEGMENTING SCRIPT FOR CATEGORY: {category}---")

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        print("Downloading NLTK punkt data...")
        nltk.download("punkt", quiet=True)

    with open(script_path, "r", encoding="utf-8") as f:
        podcast_script = json.load(f)

    max_chars = 4000  # Or load from config

    final_segments = []
    for segment in podcast_script["segments"]:
        chunks = nltk.sent_tokenize(segment["content"], language="french")
        current_chunk = ""
        for sentence in chunks:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += sentence + " "
            else:
                final_segments.append(
                    {"speaker": segment["speaker"], "content": current_chunk.strip()}
                )
                current_chunk = sentence + " "
        if current_chunk:
            final_segments.append(
                {"speaker": segment["speaker"], "content": current_chunk.strip()}
            )

    output_dir = Path(__file__).parent / "segments"
    output_dir.mkdir(exist_ok=True)
    output_file = (
        output_dir / f"segments_{category}_{datetime.now().strftime('%Y%m%d')}.json"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"segments": final_segments}, f, ensure_ascii=False, indent=2)

    print(f"---SEGMENTATION FOR {category} COMPLETE: {output_file}---")
    return {"segmented_script_path": str(output_file)}


async def synthesize_podcast_audio_node(state: AppState) -> dict:
    """
    Synthesizes audio for the podcast segments.
    """
    segmented_script_path = state["segmented_script_path"]
    category = state["current_category"]
    print(f"---SYNTHESIZING AUDIO FOR CATEGORY: {category}---")

    with open(segmented_script_path, "r", encoding="utf-8") as f:
        segments_data = json.load(f)
    segments = segments_data["segments"]

    config_path = Path(__file__).parent / "podcast_config_advanced.json"
    with open(config_path, "r", encoding="utf-8") as f:
        podcast_config = json.load(f)

    client = OpenAI(api_key=OPENAI_API_KEY)

    raw_audio_dir = Path(__file__).parent / "audio" / "raw" / category
    raw_audio_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize_segment(segment, index):
        voice_mapping = podcast_config["multi_speaker"]
        voice_id = voice_mapping.get(segment["speaker"], voice_mapping["HOST"])["voice"]

        response = await asyncio.to_thread(
            client.audio.speech.create,
            model=podcast_config["tts_settings"]["model"],
            voice=voice_id,
            input=segment["content"],
        )

        filename = raw_audio_dir / f"segment_{index:03d}.mp3"
        response.stream_to_file(str(filename))
        return str(filename)

    tasks = [synthesize_segment(seg, i) for i, seg in enumerate(segments)]
    await asyncio.gather(*tasks)

    print(f"---AUDIO SYNTHESIS FOR {category} COMPLETE---")
    return {"raw_audio_dir": str(raw_audio_dir)}


def audio_postproduction_node(state: AppState) -> dict:
    """
    Performs audio post-production to create the final episode.
    """
    raw_audio_dir = state["raw_audio_dir"]
    category = state["current_category"]
    print(f"---POST-PRODUCING AUDIO FOR CATEGORY: {category}---")

    config_path = Path(__file__).parent / "podcast_config_advanced.json"
    with open(config_path, "r", encoding="utf-8") as f:
        podcast_config = json.load(f)

    audio_files = sorted(Path(raw_audio_dir).glob("*.mp3"))
    if not audio_files:
        print(f"No raw audio files found in {raw_audio_dir}. Skipping post-production.")
        return {}

    voice_track = AudioSegment.empty()
    for audio_file in audio_files:
        voice_track += AudioSegment.from_mp3(audio_file)

    # For now, using a silent background track as a placeholder
    background_music = AudioSegment.silent(
        duration=len(voice_track) + 10000, frame_rate=24000
    )

    # Simple mix, no ducking for now
    final_audio = background_music.overlay(voice_track, position=5000)

    # Normalize
    final_audio = normalize(final_audio)

    output_dir = Path(__file__).parent / "episodes"
    output_dir.mkdir(exist_ok=True)
    output_file = (
        output_dir / f"episode_{category}_{datetime.now().strftime('%Y%m%d')}.mp3"
    )

    final_audio.export(str(output_file), format="mp3", bitrate="128k")

    print(f"---POST-PRODUCTION FOR {category} COMPLETE: {output_file}---")
    return {"final_episode_path": str(output_file)}


def upload_to_drive_node(state: AppState) -> dict:
    """
    Uploads all generated files for a category to Google Drive.
    """
    category = state["current_category"]
    print(f"---UPLOADING TO GOOGLE DRIVE FOR CATEGORY: {category}---")

    service = get_drive_service()
    if not service:
        print("Warning: Google Drive service not available, skipping upload.")
        return {}

    try:
        # Setup folder structure
        folders = setup_drive_folders(service, category)

        # Upload analysis report
        if state.get("analysis_report_path"):
            upload_to_drive(service, state["analysis_report_path"], folders["reports"])

        # Upload podcast script
        if state.get("podcast_script_path"):
            upload_to_drive(service, state["podcast_script_path"], folders["scripts"])

        # Upload segmented script
        if state.get("segmented_script_path"):
            upload_to_drive(
                service, state["segmented_script_path"], folders["segments"]
            )

        # Upload final episode
        if state.get("final_episode_path"):
            upload_to_drive(service, state["final_episode_path"], folders["episodes"])

        print(f"---GOOGLE DRIVE UPLOAD FOR {category} COMPLETE---")

    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")

    return {}


def process_category(state: AppState):
    """A sub-graph that runs the analysis and podcast generation for a single category."""
    # This function is not a node itself, but defines a sequence of nodes
    # that will be dynamically executed for each category.
    # We will construct a separate graph for this and invoke it.

    # NOTE: This approach is simpler than dynamic graphs for this specific case.
    # A full dynamic graph would involve more complex edge definitions.

    category = state["current_category"]
    print(f"\n--- Starting processing for category: {category} ---")

    analysis_state = analyze_ideas_node(state)
    state.update(analysis_state)

    # Generate Reddit images if enabled
    if state.get("reddit_image_enabled", True):
        try:
            from .nodes.reddit_image_node import generate_reddit_image_node

            image_state = generate_reddit_image_node(state)
            state.update(image_state)
            print(f"--- Reddit image generation for {category} complete ---")
        except Exception as e:
            print(f"Error generating Reddit images for {category}: {e}")

    # Run email and podcast generation in parallel
    # Since they don't depend on each other, we can just run them sequentially for simplicity
    # or use asyncio for true parallelism if they were async.
    send_email_node(state)

    podcast_state = generate_podcast_script_node(state)
    state.update(podcast_state)

    segmentation_state = semantic_segmentation_node(state)
    state.update(segmentation_state)

    # synthesize_podcast_audio_node is async
    synth_state = asyncio.run(synthesize_podcast_audio_node(state))
    state.update(synth_state)

    postprod_state = audio_postproduction_node(state)
    state.update(postprod_state)

    # Upload all files to Google Drive
    upload_to_drive_node(state)

    print(f"--- Finished processing for category: {category} ---")
    return {"branch_results": state["branch_results"] + [f"Success: {category}"]}


def main():
    # Define the graph
    workflow = StateGraph(AppState)

    # Add nodes
    workflow.add_node("collect_data", collect_data_node)

    # This is a conceptual representation. The actual branching logic is handled in the main loop.
    # LangGraph's dynamic parallelism can be complex to set up.
    # For this use case, a simple loop after the first step is more straightforward.

    # Set the entry point
    workflow.set_entry_point("collect_data")

    # A simple conditional edge that finishes the graph after collection.
    # The main logic will handle the iteration.
    workflow.add_edge("collect_data", END)

    # Compile the graph for the initial data collection step
    app = workflow.compile()

    # Load initial config
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        config_data = json.load(f)

    # Initial state
    initial_state = {
        "db_path": os.path.join(os.path.dirname(__file__), config_data["db_name"]),
        "config": config_data,
        "reddit_image_enabled": config_data.get("reddit_image_settings", {}).get(
            "enabled", True
        ),
    }

    # Run the collection part of the graph
    collect_run = app.invoke(initial_state, config={"configurable": {"thread_id": "1"}})

    # After collection, iterate through categories and process them.
    # This is our "dynamic branching".
    categories = collect_run["categories"]
    print(f"\nFound categories: {categories}")

    for category in categories:
        # Create a new state for each branch
        branch_state = collect_run.copy()
        branch_state["current_category"] = category
        process_category(branch_state)

    print("\n--- All categories processed ---")


if __name__ == "__main__":
    main()
