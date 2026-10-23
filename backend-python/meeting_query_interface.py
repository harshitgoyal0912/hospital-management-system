"""
Meeting Query Interface
======================

Easy interface to query and manage meetings stored in the database.
"""

from datetime import datetime, date, timedelta
from comprehensive_server import (
    get_meetings_by_date, 
    get_meetings_by_time_range,
    get_meeting_details,
    get_upcoming_meetings,
    update_meeting_status,
    add_meeting_notes
)
import json

class MeetingQueryInterface:
    """Simple interface for meeting queries."""
    
    def __init__(self):
        self.today = date.today()
    
    def show_todays_meetings(self):
        """Show all meetings for today."""
        print(f"📅 MEETINGS FOR TODAY ({self.today.strftime('%Y-%m-%d')})")
        print("=" * 60)
        
        result = get_meetings_by_date(self.today.strftime('%Y-%m-%d'))
        
        if result['success'] and result['total_meetings'] > 0:
            for meeting in result['meetings']:
                meeting_time = datetime.fromisoformat(meeting['meeting_datetime'])
                print(f"🕐 {meeting_time.strftime('%I:%M %p')} - {meeting['title']}")
                print(f"   📍 Location: {meeting['location']}")
                print(f"   🔗 Google Meet: {meeting['google_meet_link']}")
                print(f"   👥 Participants: {meeting['participant_count']}")
                print(f"   📋 Status: {meeting['status'].upper()}")
                print(f"   🆔 Meeting ID: {meeting['meeting_id']}")
                print("-" * 40)
        else:
            print("No meetings scheduled for today.")
        
        print()
    
    def show_tomorrows_meetings(self):
        """Show all meetings for tomorrow."""
        tomorrow = self.today + timedelta(days=1)
        print(f"📅 MEETINGS FOR TOMORROW ({tomorrow.strftime('%Y-%m-%d')})")
        print("=" * 60)
        
        result = get_meetings_by_date(tomorrow.strftime('%Y-%m-%d'))
        
        if result['success'] and result['total_meetings'] > 0:
            for meeting in result['meetings']:
                meeting_time = datetime.fromisoformat(meeting['meeting_datetime'])
                print(f"🕐 {meeting_time.strftime('%I:%M %p')} - {meeting['title']}")
                print(f"   📍 Location: {meeting['location']}")
                print(f"   🔗 Google Meet: {meeting['google_meet_link']}")
                print(f"   👥 Participants: {meeting['participant_count']}")
                print(f"   📋 Status: {meeting['status'].upper()}")
                print(f"   🆔 Meeting ID: {meeting['meeting_id']}")
                print("-" * 40)
        else:
            print("No meetings scheduled for tomorrow.")
        
        print()
    
    def show_upcoming_meetings(self, days=7):
        """Show upcoming meetings."""
        print(f"📅 UPCOMING MEETINGS (Next {days} days)")
        print("=" * 60)
        
        result = get_upcoming_meetings(days)
        
        if result['success'] and result['total_meetings'] > 0:
            for meeting in result['meetings']:
                meeting_time = datetime.fromisoformat(meeting['meeting_datetime'])
                print(f"🕐 {meeting_time.strftime('%a, %b %d - %I:%M %p')} - {meeting['title']}")
                print(f"   📍 Location: {meeting['location']}")
                print(f"   🔗 Google Meet: {meeting['google_meet_link']}")
                print(f"   👥 Participants: {meeting['participant_count']}")
                print(f"   📋 Status: {meeting['status'].upper()}")
                print(f"   🏢 Department: {meeting['department']}")
                print(f"   🆔 Meeting ID: {meeting['meeting_id']}")
                print("-" * 40)
        else:
            print(f"No meetings scheduled for the next {days} days.")
        
        print()
    
    def show_meeting_details(self, meeting_id: str):
        """Show detailed information about a specific meeting."""
        print(f"📋 MEETING DETAILS")
        print("=" * 60)
        
        result = get_meeting_details(meeting_id)
        
        if result['success']:
            meeting = result['meeting']
            meeting_time = datetime.fromisoformat(meeting['meeting_datetime'])
            
            print(f"📝 Title: {meeting['title']}")
            print(f"📅 Date & Time: {meeting_time.strftime('%A, %B %d, %Y at %I:%M %p')}")
            print(f"⏱️  Duration: {meeting['duration_minutes']} minutes")
            print(f"📍 Location: {meeting['location']}")
            print(f"🔗 Google Meet: {meeting['google_meet_link']}")
            print(f"🆔 Google Event ID: {meeting['google_event_id']}")
            print(f"📋 Status: {meeting['status'].upper()}")
            print(f"⚡ Priority: {meeting['priority'].upper()}")
            print(f"🏢 Department: {meeting['department']}")
            print(f"👤 Organizer: {meeting['organizer_name']}")
            
            print(f"\n📝 Description:")
            print(f"   {meeting['description']}")
            
            if meeting['agenda']:
                print(f"\n📋 Agenda:")
                print(f"   {meeting['agenda']}")
            
            print(f"\n👥 Participants ({meeting['participant_count']}):")
            for participant in meeting['participants']:
                print(f"   • {participant['name']} ({participant['email']}) - {participant['role']} - {participant['attendance_status']}")
            
            print(f"\n📧 Notifications:")
            print(f"   Email sent: {'✅' if meeting['email_sent'] else '❌'}")
            print(f"   Calendar invites: {'✅' if meeting['calendar_invites_sent'] else '❌'}")
            print(f"   Reminders: {'✅' if meeting['reminder_sent'] else '❌'}")
            
            if meeting['meeting_notes']:
                print(f"\n📝 Meeting Notes:")
                print(f"   {meeting['meeting_notes']}")
            
            if meeting['action_items']:
                print(f"\n✅ Action Items:")
                print(f"   {meeting['action_items']}")
            
            print(f"\n🕐 Created: {datetime.fromisoformat(meeting['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🕐 Updated: {datetime.fromisoformat(meeting['updated_at']).strftime('%Y-%m-%d %H:%M:%S')}")
            
        else:
            print(f"❌ Error: {result['message']}")
        
        print()
    
    def search_meetings_by_date(self, search_date: str):
        """Search meetings by specific date."""
        print(f"🔍 SEARCHING MEETINGS FOR {search_date}")
        print("=" * 60)
        
        result = get_meetings_by_date(search_date)
        
        if result['success'] and result['total_meetings'] > 0:
            print(f"Found {result['total_meetings']} meetings:")
            for meeting in result['meetings']:
                meeting_time = datetime.fromisoformat(meeting['meeting_datetime'])
                print(f"🕐 {meeting_time.strftime('%I:%M %p')} - {meeting['title']}")
                print(f"   🔗 Google Meet: {meeting['google_meet_link']}")
                print(f"   👥 Participants: {meeting['participant_count']}")
                print(f"   🆔 Meeting ID: {meeting['meeting_id']}")
                print("-" * 40)
        else:
            print(f"No meetings found for {search_date}")
        
        print()

def main():
    """Main interface for meeting queries."""
    query = MeetingQueryInterface()
    
    print("🏥 HOSPITAL MEETING MANAGEMENT SYSTEM")
    print("=" * 60)
    
    # Show today's meetings
    query.show_todays_meetings()
    
    # Show upcoming meetings
    query.show_upcoming_meetings(3)  # Next 3 days
    
    print("📖 AVAILABLE COMMANDS:")
    print("• query.show_todays_meetings()")
    print("• query.show_tomorrows_meetings()")
    print("• query.show_upcoming_meetings(days=7)")
    print("• query.show_meeting_details('meeting-id-here')")
    print("• query.search_meetings_by_date('2025-08-07')")
    print()
    
    return query

if __name__ == "__main__":
    query_interface = main()
    
    # Example: Show details of the most recent meeting if available
    result = get_upcoming_meetings(1)
    if result['success'] and result['total_meetings'] > 0:
        first_meeting_id = result['meetings'][0]['meeting_id']
        print("🔍 SHOWING DETAILS OF MOST RECENT MEETING:")
        query_interface.show_meeting_details(first_meeting_id)
