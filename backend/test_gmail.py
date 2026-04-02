from gmail_service import get_gmail_service
try:
    print("Attempting to get service...")
    service = get_gmail_service()
    print("Service obtained successfully.")
    results = service.users().messages().list(userId='me', maxResults=1).execute()
    print(f"Messages call result: {results}")
except Exception as e:
    print(f"Error: {e}")
