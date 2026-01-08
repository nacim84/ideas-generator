import os
import base64
import json
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import markdown

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Paths to credentials (at root of project)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TOKEN_PATH = os.path.join(ROOT_DIR, 'token.json')
CREDENTIALS_PATH = os.path.join(ROOT_DIR, 'credentials.json')

def get_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"Error: {CREDENTIALS_PATH} not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def send_message(service, sender, to, subject, message_text):
    message = MIMEText(message_text, 'html') # Sending as HTML to preserve some formatting if we convert MD
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    try:
        message = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print(f"Message Id: {message['id']} sent successfully.")
        return message
    except Exception as error:
        print(f"An error occurred: {error}")
        return None

def main():
    if not RECIPIENT_EMAIL:
        print("Error: RECIPIENT_EMAIL not set in .env")
        return

    # Read the analysis report
    report_path = os.path.join(os.path.dirname(__file__), 'latest_analysis.md')
    if not os.path.exists(report_path):
        print("Error: No analysis report found. Run analyze_ideas.py first.")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert Markdown to HTML for nicer email
    html_content = markdown.markdown(md_content)

    print("Authenticating with Gmail...")
    service = get_service()
    if not service:
        print("Failed to authenticate.")
        return

    print(f"Sending email to {RECIPIENT_EMAIL}...")
    send_message(
        service, 
        "me", 
        RECIPIENT_EMAIL, 
        "Daily Reddit Business Ideas", 
        f"<html><body>{html_content}</body></html>"
    )

if __name__ == "__main__":
    main()
