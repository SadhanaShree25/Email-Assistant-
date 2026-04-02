import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')

from auth_service import get_creds

def get_gmail_service(user_id="default_user"):
    creds = get_creds(user_id)
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_text_from_payload(payload):
    """Recursively extract text from Gmail payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            text = get_text_from_payload(part)
            if text:
                return text
    if payload.get('mimeType') == 'text/plain':
        data = payload.get('body', {}).get('data')
        if data:
            # Fix padding for base64 decoding
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            return base64.urlsafe_b64decode(data).decode('utf-8')
    return None

def fetch_emails(max_results=10, user_id="default_user"):
    try:
        service = get_gmail_service(user_id)
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])

        email_data = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            
            headers = msg['payload'].get('headers', [])
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), "No Subject")
            sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), "Unknown")
            message_id = next((header['value'] for header in headers if header['name'].lower() == 'message-id'), message['id'])
            
            # Extract content using improved helper
            content = get_text_from_payload(msg['payload']) or msg.get('snippet', '')
            
            email_data.append({
                "Subject": subject,
                "From": sender,
                "Message-ID": message_id,
                "message": content
            })
            
        return email_data
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e

from email.mime.text import MIMEText

def send_email(to: str, subject: str, message_text: str, user_id="default_user") -> str:
    """Send an email using the Gmail API."""
    try:
        service = get_gmail_service(user_id)
        
        message = MIMEText(message_text)
        message['to'] = to
        message['subject'] = subject
        
        # Create the raw message string
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        sent_message = service.users().messages().send(
            userId='me', 
            body={'raw': raw}
        ).execute()
        
        return f"Email sent successfully to {to}. ID: {sent_message['id']}"
    except Exception as e:
        return f"Error sending email: {str(e)}"
