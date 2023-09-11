import datetime
import json
from typing import Optional

from pywebpush import webpush

from rezervo.consts import WEEKDAYS
from rezervo.errors import AuthenticationError, BookingError
from rezervo.schemas.config.config import PushNotificationSubscription
from rezervo.schemas.config.user import Class
from rezervo.schemas.schedule import RezervoClass
from rezervo.settings import get_settings
from rezervo.utils.logging_utils import err

AUTH_FAILURE_REASONS = {
    AuthenticationError.INVALID_CREDENTIALS: "Ugyldig brukernavn eller passord 🔐",
    AuthenticationError.AUTH_TEMPORARILY_BLOCKED: "Midlertidig utestengt ⛔",
    AuthenticationError.TOKEN_EXTRACTION_FAILED: "Klarte ikke å hente autentiseringsnøkkel 🕵️",
    AuthenticationError.TOKEN_VALIDATION_FAILED: "Klarte ikke å verifisere autentiseringsnøkkel ‽",
}

BOOKING_FAILURE_REASONS = {
    BookingError.CLASS_MISSING: "Fant ikke timen 🕵",
    BookingError.INCORRECT_START_TIME: "Feil starttid 🕖",
    BookingError.MISSING_SCHEDULE_DAY: "Fant ikke riktig dag 📅🔍",
    BookingError.TOO_LONG_WAITING_TIME: "Ventetid før booking var for lang 💤",
    BookingError.INVALID_CONFIG: "Ugyldig bookingkonfigurasjon 💔",
}


def notify_web_push(subscription: PushNotificationSubscription, message: str) -> bool:
    settings = get_settings()
    res = webpush(
        subscription_info=subscription.dict(),
        data=json.dumps({"title": "rezervo", "message": message}),
        vapid_private_key=settings.WEB_PUSH_PRIVATE_KEY,
        vapid_claims={"sub": f"mailto:{settings.WEB_PUSH_EMAIL}"},
    )
    return res.ok


def notify_booking_web_push(
    subscription: PushNotificationSubscription, booked_class: RezervoClass
) -> None:
    if not notify_web_push(
        subscription,
        f"{booked_class.name} ({booked_class.from_field[:-3]}, {booked_class.studio.name}) er booket",
    ):
        err.log("Failed to send booking notification via web push")
        return
    print("Booking notification posted successfully via web push")
    return


def notify_booking_failure_web_push(
    subscription: PushNotificationSubscription,
    _class_config: Optional[Class] = None,
    error: Optional[BookingError] = None,
    check_run: bool = False,
) -> None:
    if _class_config is None:
        msg = (
            f"{'⚠️ Forhåndssjekk feilet!' if check_run else '😵'} Klarte ikke å booke time"
            f". {BOOKING_FAILURE_REASONS[error]}"
            if error in BOOKING_FAILURE_REASONS
            else ""
        )
    else:
        class_name = f"{_class_config.display_name if _class_config.display_name is not None else _class_config.activity}"
        class_time = (
            f"{WEEKDAYS[_class_config.weekday].lower()} "
            f"{datetime.time(_class_config.time.hour, _class_config.time.minute).strftime('%H:%M')}"
        )
        msg = (
            f"{'⚠️ Forhåndssjekk feilet! Kan ikke booke' if check_run else '😵 Klarte ikke å booke'} "
            f"{class_name} ({class_time})"
            f"{f'. {BOOKING_FAILURE_REASONS[error]}' if error in BOOKING_FAILURE_REASONS else ''}"
        )
    print(
        f"Posting booking {'check ' if check_run else ''}failure notification via web push"
    )
    if not notify_web_push(subscription, msg):
        err.log("Failed to send booking failure notification via web push")
        return
    print("Booking failure notification posted successfully via web push")
    return


def notify_auth_failure_web_push(
    subscription: PushNotificationSubscription,
    error: Optional[AuthenticationError] = None,
    check_run: bool = False,
) -> None:
    msg = (
        f"{'⚠️ Forhåndssjekk feilet!' if check_run else '😵'} Klarte ikke å logge inn"
        f". {AUTH_FAILURE_REASONS[error]}"
        if error in AUTH_FAILURE_REASONS
        else ""
    )
    print(
        f"Posting auth {'check ' if check_run else ''}failure notification via web push"
    )
    if not notify_web_push(subscription, msg):
        err.log("Failed to send auth failure notification via web push")
        return
    print(
        f"Auth {'check ' if check_run else ''}failure notification posted successfully via web push"
    )
    return
