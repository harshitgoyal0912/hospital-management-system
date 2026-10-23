"""Meeting Management Agent - schedules meetings and manages meeting data."""
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

try:
    from meeting_scheduler import MeetingSchedulerAgent
    from meeting_management import MeetingManager
    from database import SessionLocal
    MEETING_DEPS = True
except ImportError:
    MEETING_DEPS = False

class MeetingAgent(BaseAgent):
    """Agent for meeting scheduling & retrieval (wraps MeetingSchedulerAgent / MeetingManager)."""
    def __init__(self):
        super().__init__("Meeting Scheduling Agent", "meeting_agent")
        self.scheduler = MeetingSchedulerAgent() if MEETING_DEPS else None
        self.manager = MeetingManager() if MEETING_DEPS else None

    def get_tools(self) -> List[str]:
        return [
            "schedule_meeting",            # Natural language scheduling
            "list_meetings",              # List meetings by date / upcoming
            "get_meeting_by_id",          # Detailed meeting info
            "update_meeting_status",      # Change status
            "add_meeting_notes",          # Post-meeting notes/action items
            "update_meeting",             # Update meeting date/time and notify participants
            "cancel_meeting",             # Cancel meeting and notify participants
            "postpone_meeting"            # Postpone meeting to a new date/time
        ]

    def get_capabilities(self) -> List[str]:
        return [
            "Natural language meeting scheduling with Google Meet + email",
            "Meeting storage & participant management",
            "Status / notes updates",
            "Meeting rescheduling with automatic participant notifications",
            "Meeting cancellation with participant notifications",
            "Meeting postponement to new dates/times",
        ]

    # ---- Tool Implementations ----
    def schedule_meeting(self, query: str) -> Dict[str, Any]:
        if not MEETING_DEPS or not self.scheduler:
            return {"success": False, "message": "Meeting dependencies not available"}
        result = self.scheduler.schedule_meeting(query)
        self.log_interaction(query=f"Schedule meeting: {query}", response=result.get("message",""), tool_used="schedule_meeting")
        return result

    def list_meetings(self, date_str: str = None, days_ahead: int = 7) -> Dict[str, Any]:
        if not MEETING_DEPS or not self.manager:
            return {"success": False, "message": "Meeting dependencies not available"}
        try:
            # Close and recreate the session to ensure we see latest data
            self.manager.session.close()
            from database import SessionLocal
            self.manager.session = SessionLocal()
            
            if date_str:
                target = datetime.strptime(date_str, "%Y-%m-%d").date()
                meetings = self.manager.get_meetings_by_date(target)
            else:
                meetings = self.manager.get_upcoming_meetings(days_ahead)
            data = []
            for m in meetings:
                data.append({
                    "meeting_id": str(m.id),
                    "title": m.title,
                    "meeting_datetime": m.meeting_datetime.isoformat(),
                    "duration_minutes": m.duration_minutes,
                    "location": m.location,
                    "google_meet_link": m.google_meet_link,
                    "status": m.status,
                    "priority": m.priority,
                })
            return {"success": True, "meetings": data, "total_meetings": len(data)}
        except Exception as e:
            return {"success": False, "message": f"Failed to list meetings: {e}"}

    def get_meeting_by_id(self, meeting_id: str) -> Dict[str, Any]:
        if not MEETING_DEPS or not self.manager:
            return {"success": False, "message": "Meeting dependencies not available"}
        try:
            # Close and recreate the session to ensure we see latest data
            self.manager.session.close()
            from database import SessionLocal
            self.manager.session = SessionLocal()
            
            m = self.manager.get_meeting_by_id(meeting_id)
            if not m:
                return {"success": False, "message": "Meeting not found"}
            participants = self.manager.get_meeting_participants(meeting_id)
            return {"success": True, "data": {
                "meeting_id": str(m.id),
                "title": m.title,
                "meeting_datetime": m.meeting_datetime.isoformat(),
                "duration_minutes": m.duration_minutes,
                "location": m.location,
                "google_meet_link": m.google_meet_link,
                "status": m.status,
                "priority": m.priority,
                "agenda": m.agenda,
                "meeting_notes": m.meeting_notes,
                "action_items": m.action_items,
                "participants": participants,
            }}
        except Exception as e:
            return {"success": False, "message": f"Failed to get meeting: {e}"}

    def update_meeting_status(self, meeting_id: str, status: str) -> Dict[str, Any]:
        if not MEETING_DEPS or not self.manager:
            return {"success": False, "message": "Meeting dependencies not available"}
        ok = self.manager.update_meeting_status(meeting_id, status)
        return {"success": ok, "message": "Status updated" if ok else "Failed to update status"}

    def update_meeting(self, query: str) -> Dict[str, Any]:
        """Update meeting date/time and send updated emails to participants."""
        if not MEETING_DEPS or not self.scheduler:
            return {"success": False, "message": "Meeting dependencies not available"}
        result = self.scheduler.update_meeting(query)
        self.log_interaction(query=f"Update meeting: {query}", response=result.get("message",""), tool_used="update_meeting")
        return result

    def add_meeting_notes(self, meeting_id: str, notes: str, action_items: str = None) -> Dict[str, Any]:
        if not MEETING_DEPS or not self.manager:
            return {"success": False, "message": "Meeting dependencies not available"}
        ok = self.manager.add_meeting_notes(meeting_id, notes, action_items)
        return {"success": ok, "message": "Notes saved" if ok else "Failed to save notes"}

    def cancel_meeting(self, query: str) -> Dict[str, Any]:
        """Cancel a meeting and notify participants using natural language query."""
        if not MEETING_DEPS or not self.scheduler:
            return {"success": False, "message": "Meeting dependencies not available"}
        
        # Use the update_meeting method with cancellation keywords
        # The cancellation logic is already implemented in update_meeting
        cancel_query = f"cancel {query}" if not any(word in query.lower() for word in ['cancel', 'cancelled', 'abort', 'call off']) else query
        
        result = self.scheduler.update_meeting(cancel_query)
        self.log_interaction(query=f"Cancel meeting: {query}", response=result.get("message",""), tool_used="cancel_meeting")
        return result

    def postpone_meeting(self, query: str) -> Dict[str, Any]:
        """Postpone a meeting to a new date/time and notify participants using natural language query."""
        if not MEETING_DEPS or not self.scheduler:
            return {"success": False, "message": "Meeting dependencies not available"}
        
        # Use the update_meeting method for postponement/rescheduling
        # The rescheduling logic is already implemented in update_meeting
        result = self.scheduler.update_meeting(query)
        self.log_interaction(query=f"Postpone meeting: {query}", response=result.get("message",""), tool_used="postpone_meeting")
        return result
