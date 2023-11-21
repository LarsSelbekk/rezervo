import secrets
from datetime import datetime, timedelta
from typing import Optional

import pytz
from icalendar import cal  # type: ignore[import]

from rezervo.models import SessionState
from rezervo.schemas.config.config import ConfigValue
from rezervo.schemas.schedule import UserSession
from rezervo.utils.str_utils import format_name_list_to_natural


def generate_calendar_token():
    return secrets.token_urlsafe()


def ical_event_from_session(
    session: UserSession, config: ConfigValue, timezone: str
) -> Optional[cal.Event]:
    _class = session.class_data
    if _class is None:
        return None
    event = cal.Event()
    event.add("uid", f"{session.chain}-{_class.id}-{session.user_id}@rezervo.no")
    event.add("summary", _class.activity.name)
    instructors_str = (
        f"med {format_name_list_to_natural([i.name for i in _class.instructors])}"
        if len(_class.instructors) > 0
        else ""
    )
    event.add(
        "description",
        f"{_class.activity.name} {instructors_str}",
    )
    event.add("location", f"{_class.location.studio} ({_class.location.room})")
    # TODO: start and end times use a naughty timezone hack to make ical valid, check if any nicer solutions exists
    tz = pytz.timezone(timezone)
    event.add("dtstart", _class.start_time.astimezone(tz).replace(tzinfo=None))
    event.add("dtend", _class.end_time.astimezone(tz).replace(tzinfo=None))
    event.add("dtstamp", datetime.now())
    event.add(
        "status",
        "CONFIRMED"
        if session.status in [SessionState.BOOKED, SessionState.CONFIRMED]
        else "TENTATIVE",
    )
    if (
        config.notifications is not None
        and config.notifications.reminder_hours_before is not None
    ):
        alarm = cal.Alarm()
        minutes = round(config.notifications.reminder_hours_before * 60)
        # This doesn't seem to work in a calendar subscription feed. Tested on Outlook (new version of Windows Mail),
        # Google Calendar. Tried adding UID and X-WR-ALARMUID, didn't help. Also tried changing action to DISPLAY,
        # no dice. From an internet search, it just doesn't seem to be supported.
        alarm.add("trigger", timedelta(minutes=-minutes))
        alarm.add("action", "AUDIO")
        event.add_component(alarm)
    event.add(
        "sequence",
        # Not strictly compliant, but the status will generally follow this order (except UNKNOWN)
        # so the sequence number will most likely increase monotonically
        {
            SessionState.UNKNOWN: 0,
            SessionState.PLANNED: 1,
            SessionState.WAITLIST: 2,
            SessionState.BOOKED: 3,
            SessionState.CONFIRMED: 4,
        }[session.status],
    )
    return event
