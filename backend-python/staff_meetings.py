"""Staff Meeting table and related functionality."""

from datetime import datetime

# Import models from database.py instead of redefining them
from database import StaffMeeting, StaffMeetingParticipant

# All staff meeting functionality now uses the models from database.py
# This prevents the "Table already defined" error that was occurring
# when the same table was defined in both database.py and this file.
