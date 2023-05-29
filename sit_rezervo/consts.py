WEEKDAYS = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]

AUTH_URL = "https://www.sit.no/"
BOOKING_URL = "https://www.sit.no/trening/gruppe"
MY_SESSIONS_URL = "https://www.sit.no/ibooking-api/callback/get-my-sessions"

ADD_BOOKING_URL = "https://ibooking.sit.no/webapp/api//Schedule/addBooking"
CANCEL_BOOKING_URL = "https://ibooking.sit.no/webapp/api//Schedule/cancelBooking"
CLASSES_SCHEDULE_URL = 'https://ibooking.sit.no/webapp/api/Schedule/getSchedule'
CLASS_URL = 'https://ibooking.sit.no/webapp/api/Schedule/getClass'
TOKEN_VALIDATION_URL = "https://ibooking.sit.no/webapp/api/User/validateToken"
ICAL_URL = "https://ibooking.sit.no/webapp/api/Schedule/calendar"

SLACK_ACTION_ADD_BOOKING_TO_CALENDAR = "add_booking_to_calendar"
SLACK_ACTION_CANCEL_BOOKING = "cancel_booking"

CRON_PULL_SESSIONS_JOB_COMMENT = "pull sessions"
CRON_PULL_SESSIONS_SCHEDULE = "2,17,32,47 4-23 * * *"