"""Proper Google Meet Integration using Google Calendar API

This creates REAL Google Meet links through Google Calendar API.
"""

import os
import pickle
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

# Google API imports (install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
    print("Google API libraries imported successfully")
except ImportError as e:
    GOOGLE_APIS_AVAILABLE = False
    print(f"Google API libraries not installed: {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    # Create dummy functions for fallback
    Request = None
    Credentials = None
    InstalledAppFlow = None
    build = None
    HttpError = Exception

class GoogleMeetAPIIntegration:
    """Real Google Meet integration using Google Calendar API."""
    
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, interactive=False):
        self.service = None
        self.credentials = None
        self.calendar_service = None
        self.setup_credentials(interactive)
    
    def setup_credentials(self, interactive=True):
        """Set up Google API credentials."""
        if not GOOGLE_APIS_AVAILABLE:
            print("Google API libraries not available - using fallback mode")
            return False
            
        try:
            creds = None
            token_file = Path("token.pickle")
            credentials_file = Path("credentials.json")
            
            # The file token.pickle stores the user's access and refresh tokens.
            if token_file.exists():
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("Refreshing Google API credentials...")
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        print(f"Token refresh failed: {e}")
                        if not interactive:
                            print("Running in non-interactive mode - skipping OAuth")
                            return False
                        creds = None
                else:
                    if not credentials_file.exists():
                        print("credentials.json not found!")
                        if interactive:
                            print("Please download credentials.json from Google Cloud Console")
                            print("1. Go to: https://console.cloud.google.com/apis/credentials")
                            print("2. Create OAuth 2.0 Client ID")
                            print("3. Download as credentials.json")
                        return False
                    
                    if not interactive:
                        print("OAuth required but running in non-interactive mode")
                        return False
                    
                    print("Setting up Google OAuth...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                if creds:
                    with open(token_file, 'wb') as token:
                        pickle.dump(creds, token)
            
            self.credentials = creds
            if creds:
                self.service = build('calendar', 'v3', credentials=creds)
                self.calendar_service = self.service  # Also set this alias
                print("Google Calendar API initialized successfully")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error setting up Google credentials: {e}")
            return False
    
    def create_meet_event(self, 
                         title: str,
                         description: str,
                         start_time: datetime,
                         duration_minutes: int = 30,
                         attendees: List[str] = None) -> Dict[str, Any]:
        """Create a Google Calendar event with Google Meet link."""
        
        if not self.service:
            return {"error": "Google Calendar API not initialized"}
        
        try:
            # Calculate end time
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Prepare attendees list
            attendee_list = []
            if attendees:
                for email in attendees:
                    attendee_list.append({'email': email})
            
            # Create the event
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': attendee_list,
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"hospital-meeting-{int(datetime.now().timestamp())}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 10},       # 10 minutes before
                    ],
                },
            }
            
            # Create the event
            print("Creating Google Calendar event with Meet link...")
            event_result = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1  # Required for Google Meet integration
            ).execute()
            
            # Extract the Google Meet link
            meet_link = None
            if 'conferenceData' in event_result and 'entryPoints' in event_result['conferenceData']:
                for entry_point in event_result['conferenceData']['entryPoints']:
                    if entry_point['entryPointType'] == 'video':
                        meet_link = entry_point['uri']
                        break
            
            result = {
                'event_id': event_result['id'],
                'event_link': event_result.get('htmlLink'),
                'meet_link': meet_link,
                'title': title,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'attendees_count': len(attendee_list),
                'created_at': datetime.now().isoformat()
            }
            
            print(f"Google Meet event created successfully!")
            print(f"Event ID: {event_result['id']}")
            print(f"Meet Link: {meet_link}")
            
            return result
            
        except HttpError as error:
            print(f"Google Calendar API error: {error}")
            return {"error": f"Google Calendar API error: {error}"}
        except Exception as e:
            print(f"Error creating Google Meet event: {e}")
            return {"error": f"Error creating event: {e}"}
    
    def create_instant_meet_room(self, title: str = "Hospital Meeting") -> str:
        """Create an instant Google Meet room for immediate use."""
        try:
            # Create an event starting now for instant meeting
            now = datetime.now()
            
            result = self.create_meet_event(
                title=title,
                description="Instant hospital meeting room",
                start_time=now,
                duration_minutes=60  # 1 hour default
            )
            
            if 'meet_link' in result and result['meet_link']:
                print(f"Instant Google Meet room created: {result['meet_link']}")
                return result['meet_link']
            else:
                print("Failed to create instant Google Meet room")
                return "https://meet.google.com/new"
                
        except Exception as e:
            print(f"Error creating instant meet room: {e}")
            return "https://meet.google.com/new"
    
    def test_integration(self):
        """Test the Google Meet integration."""
        print("Testing Google Meet API Integration...")
        print("=" * 50)
        
        if not self.service:
            print("Google Calendar API not available")
            return False
        
        try:
            # Test creating a meeting
            test_time = datetime.now() + timedelta(minutes=10)
            result = self.create_meet_event(
                title="Test Hospital Meeting",
                description="Testing Google Meet integration",
                start_time=test_time,
                duration_minutes=15,
                attendees=["test@example.com"]
            )
            
            if 'meet_link' in result and result['meet_link']:
                print("Google Meet integration working!")
                print(f"Test meet link: {result['meet_link']}")
                return True
            else:
                print("Failed to create Google Meet link")
                return False
                
        except Exception as e:
            print(f"Test failed: {e}")
            return False

def setup_google_meet():
    """Setup function to guide user through Google Meet configuration."""
    print("Google Meet Setup Guide")
    print("=" * 50)
    
    print("""
STEP 1: Google Cloud Console Setup
1. Go to: https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable Google Calendar API:
   - Go to APIs & Services > Library
   - Search for "Google Calendar API"
   - Click Enable

STEP 2: Create Credentials
1. Go to APIs & Services > Credentials
2. Click "Create Credentials" > "OAuth 2.0 Client ID"
3. If prompted, configure OAuth consent screen first
4. Choose "Desktop Application"
5. Download the JSON file as 'credentials.json'
6. Place 'credentials.json' in this directory

STEP 3: Install Dependencies
Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

STEP 4: First Run
When you first run the integration, it will:
1. Open a web browser for OAuth authentication
2. Ask you to sign in to your Google account
3. Request permission to access Google Calendar
4. Save credentials for future use
""")
    
    # Check if credentials exist
    if Path("credentials.json").exists():
        print("credentials.json found!")
        
        # Try to initialize the integration
        try:
            integration = GoogleMeetAPIIntegration()
            if integration.service:
                print("Google Meet integration ready!")
                return True
            else:
                print("Failed to initialize Google Meet integration")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    else:
        print("credentials.json not found")
        print("Please download credentials.json from Google Cloud Console")
        return False

# Create alias for backwards compatibility
GoogleMeetAPI = GoogleMeetAPIIntegration

if __name__ == "__main__":
    setup_google_meet()
