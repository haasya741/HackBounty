import logging
import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Dict, Any, List
from config import CALENDAR_API_SCOPES, CALENDAR_ID

logger = logging.getLogger('HackBountyAgent.Calendar')

class CalendarManager:
    """
    Manages authentication and scheduling of events using the Google Calendar API.
    """
    def __init__(self):
        self.service = self._authenticate_calendar()

    def _authenticate_calendar(self):
        """
        Handles the OAuth 2.0 flow. Tries to load existing token, otherwise
        prompts the user to authorize and saves the new token.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', CALENDAR_API_SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Token expired, refreshing...")
                creds.refresh(Request())
            else:
                logger.warning("No valid token found. Starting OAuth flow.")
                # The credentials.json file must be downloaded from Google Cloud Console
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', CALENDAR_API_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    logger.error("FATAL: 'credentials.json' not found. Cannot authenticate Google Calendar.")
                    return None
                except Exception as e:
                    logger.error(f"Error during OAuth flow: {e}")
                    return None
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            # Build the service object
            service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar service built successfully.")
            return service
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service: {e}")
            return None

    def create_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Creates an event in the user's primary Google Calendar.
        """
        if not self.service:
            logger.error(f"Cannot create event: Calendar service not available.")
            return False

        # Event body structure for Google Calendar API
        event = {
            'summary': f"[HackBounty] {event_data['title']}",
            'location': 'Online/Check Link',
            'description': (
                f"{event_data['description']}\n\n"
                f"Topic Relevance Score: {event_data['similarity_score']}\n"
                f"Event Link: {event_data['link']}\n"
                f"**IMPORTANT: Check deadline on event link!**"
            ),
            'start': {
                'dateTime': event_data['start_time'], # e.g., '2025-11-15T09:00:00'
                'timeZone': 'America/Los_Angeles', # Customize time zone if known
            },
            'end': {
                'dateTime': event_data['end_time'],
                'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60}, # 1 day prior
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }

        try:
            # Insert the event into the calendar
            event = self.service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            logger.info(f"Event created: '{event_data['title']}' at {event.get('htmlLink')}")

            # Also create a separate reminder for the deadline
            self._create_deadline_reminder(event_data)

            return True

        except HttpError as e:
            logger.error(f"HTTP Error creating event for '{event_data['title']}': {e}")
            return False
        except Exception as e:
            logger.error(f"Generic error creating event for '{event_data['title']}': {e}")
            return False

    def _create_deadline_reminder(self, event_data: Dict[str, Any]):
        """Creates a separate, all-day event for the application deadline."""
        deadline_dt = datetime.datetime.fromisoformat(event_data['deadline']).date()
        
        # Create an all-day event that spans one day (the day of the deadline)
        deadline_event = {
            'summary': f"[HackBounty DEADLINE] Apply for: {event_data['title']}",
            'description': f"Link: {event_data['link']}",
            'start': {
                'date': deadline_dt.isoformat(), # All-day event starts on this date
            },
            'end': {
                'date': (deadline_dt + datetime.timedelta(days=1)).isoformat(), # Ends the next day
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 7 * 24 * 60}, # 7 days prior
                    {'method': 'popup', 'minutes': 3 * 24 * 60}, # 3 days prior
                ],
            },
        }
        
        try:
            self.service.events().insert(calendarId=CALENDAR_ID, body=deadline_event).execute()
            logger.info(f"Deadline reminder created for: {event_data['title']}")
        except HttpError as e:
            logger.error(f"HTTP Error creating deadline reminder for '{event_data['title']}': {e}")
        except Exception as e:
            logger.error(f"Generic error creating deadline reminder for '{event_data['title']}': {e}")
