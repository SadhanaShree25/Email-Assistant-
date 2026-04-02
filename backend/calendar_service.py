from googleapiclient.discovery import build
from auth_service import get_creds
from datetime import datetime, timedelta

def get_calendar_service(user_id="default_user"):
    creds = get_creds(user_id)
    service = build('calendar', 'v3', credentials=creds)
    return service

def read_calendar(date_str: str, user_id="default_user") -> str:
    """Read the calendar events for a specific date (YYYY-MM-DD)."""
    try:
        service = get_calendar_service(user_id)
        
        # Define the time range for the day
        start_time = f"{date_str}T00:00:00Z"
        end_time = f"{date_str}T23:59:59Z"
        
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=start_time,
            timeMax=end_time, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return f"You have no events scheduled for {date_str}."

        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            event_list.append(f"{start}: {summary}")
            
        return f"Events for {date_str}:\n" + "\n".join(event_list)
    except Exception as e:
        return f"Error reading calendar: {str(e)}"

def create_calendar_invite(title: str, date_str: str, time_str: str = "10:00:00", duration_minutes: int = 30, user_id="default_user") -> str:
    """Create a calendar event for a specific date and time."""
    try:
        service = get_calendar_service(user_id)
        
        start_dt = f"{date_str}T{time_str}Z"
        # Calculate end time
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        end_dt_obj = dt + timedelta(minutes=duration_minutes)
        end_dt = end_dt_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

        event = {
            'summary': title,
            'start': {
                'dateTime': start_dt,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_dt,
                'timeZone': 'UTC',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Event created: {event.get('htmlLink')}"
    except Exception as e:
        return f"Error creating calendar event: {str(e)}"
