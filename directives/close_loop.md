# Directive: Close The Loop

## Goal
Proactively notify users when the specific issue they reported (Bug or Feature Request) has been resolved.

## Trigger
- Run this workflow daily or on-demand.

## Steps

1.  **Find Resolved Issues**
    - Query the system for tickets that have moved to `DONE` status since the last check.
    - Run: `execution/ticket_manager.py get_resolved_tickets`
    - **Output**: JSON list of tickets, e.g., `[{ "id": "TICKET-123", "summary": "Fix login bug", "linked_users": ["@haxor44", "@dev_guru"] }]`

2.  **Notify Users**
    - For EACH user in `linked_users` for EACH ticket:
        - Draft a personalized response.
        - **Context**: "You reported <ticket_summary>".
        - **Update**: "It is fixed/shipped."
        - Run: `execution/post_reply.py <user_handle> <ticket_id> "<drafted_message>"`

3.  **Update Notification Status**
    - Mark the user as "Notified" for that ticket to prevent duplicate messages (handled implicitly by the script or a separate flag if needed).

## Success Criteria
- All users linked to a resolved ticket receive a notification.
- No user receives the same notification twice.
- Tone is helpful, personal, and brief.
