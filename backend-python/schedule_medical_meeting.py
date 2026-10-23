from meeting_scheduler import MeetingSchedulerAgent

print("Scheduling medical equipment meeting for August 15th, 2025...")

agent = MeetingSchedulerAgent()
result = agent.schedule_meeting("Schedule medical equipment and sales inventory improvement meeting for all staff on 2025/08/15 at 4pm for 30 minutes")

print("Success:", result.get("success"))
print("Message:", result.get("message", "No message"))

if result.get("success"):
    print("✅ Meeting scheduled successfully!")
    print("✅ Google Meet link created and emails sent to all staff!")
else:
    print("❌ Error occurred:", result.get("message"))
