import json
import time
from datetime import datetime
from typing import Union

import pytz
import requests
from requests import Session

from rezervo.consts import WEEKDAYS
from rezervo.errors import AuthenticationError, BookingError
from rezervo.integrations.fsc.auth import authenticate_session, fetch_user_details
from rezervo.integrations.fsc.schedule import fetch_fsc_schedule
from rezervo.integrations.fsc.schema import (
    BookingsResponse,
    BookingType,
    rezervo_class_from_fsc_class,
)
from rezervo.notify.notify import notify_booking
from rezervo.schemas.config.config import ConfigValue
from rezervo.schemas.config.user import Class, IntegrationUser
from rezervo.schemas.schedule import RezervoClass
from rezervo.utils.logging_utils import err
from rezervo.utils.str_utils import format_name_list_to_natural


def booking_url(auth_session: Session) -> Union[str, AuthenticationError]:
    user_details = fetch_user_details(auth_session)
    if isinstance(auth_session, AuthenticationError):
        return auth_session
    return f"https://fsc.no/api/v1/auth/customers/{user_details['id']}/bookings/groupactivities"


def find_fsc_class_by_id(
    integration_user: IntegrationUser, config: ConfigValue, class_id: str
) -> Union[RezervoClass, None, BookingError, AuthenticationError]:
    print(f"Searching for class by id: {class_id}")
    fsc_schedule = fetch_fsc_schedule()
    if fsc_schedule is None:
        err.log("Class get request failed")
        return BookingError.ERROR
    fsc_class = next(
        (c for c in fsc_schedule if c.id == int(class_id)),
        None,
    )
    if fsc_class is None:
        return BookingError.CLASS_MISSING
    return rezervo_class_from_fsc_class(fsc_class)


def find_fsc_class(
    _class_config: Class,
) -> Union[RezervoClass, BookingError, AuthenticationError]:
    print(f"Searching for class matching config: {_class_config}")
    schedule = fetch_fsc_schedule()
    if schedule is None:
        err.log("Schedule get request denied")
        return BookingError.ERROR
    if not 0 <= _class_config.weekday < len(WEEKDAYS):
        err.log(f"Invalid weekday number ({_class_config.weekday=})")
        return BookingError.MALFORMED_SEARCH

    result = None
    for c in schedule:
        if c.groupActivityProduct.id != _class_config.activity:
            continue
        start_time = datetime.fromisoformat(c.duration.start.replace("Z", "")[:-4])
        utc_start_time = pytz.timezone("UTC").localize(start_time)
        localized_start_time = utc_start_time.astimezone(pytz.timezone("Europe/Oslo"))
        time_matches = (
            localized_start_time.hour == _class_config.time.hour
            and localized_start_time.minute == _class_config.time.minute
        )
        if not time_matches:
            print(f"Found class, but start time did not match: {c}")
            result = BookingError.INCORRECT_START_TIME
            continue
        if localized_start_time.weekday() != _class_config.weekday:
            print(f"Found class, but weekday did not match: {c}")
            result = BookingError.MISSING_SCHEDULE_DAY
            continue
        search_feedback = f'Found class: "{c.name}"'
        if len(c.instructors) > 0:
            search_feedback += (
                f" with {format_name_list_to_natural([i.name for i in c.instructors])}"
            )
        else:
            search_feedback += " (missing instructor)"
        search_feedback += f" at {c.duration.start}"
        print(search_feedback)
        return rezervo_class_from_fsc_class(c)
    err.log("Could not find class matching criteria")
    if result is None:
        result = BookingError.CLASS_MISSING
    return result


def book_fsc_class(auth_session: Session, class_id: int) -> bool:
    print(f"Booking class {class_id}")
    response = auth_session.post(
        booking_url(auth_session),
        json.dumps({"groupActivity": class_id, "allowWaitingList": True}),
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 201:
        err.log("Booking attempt failed: " + response.text)
        return False
    return True


def try_book_fsc_class(
    integration_user: IntegrationUser, _class: RezervoClass, config: ConfigValue
) -> Union[None, BookingError, AuthenticationError]:
    max_attempts = config.booking.max_attempts
    if max_attempts < 1:
        err.log("Max booking attempts should be a positive number")
        return BookingError.INVALID_CONFIG
    print("Authenticating...")
    auth_session = authenticate_session(
        integration_user.username, integration_user.password
    )
    if isinstance(auth_session, AuthenticationError):
        err.log("Authentication failed")
        return auth_session
    booked = False
    attempts = 0
    while not booked:
        booked = book_fsc_class(auth_session, _class.id)
        attempts += 1
        if booked:
            break
        if attempts >= max_attempts:
            break
        sleep_seconds = 2**attempts
        print(f"Exponential backoff, retrying in {sleep_seconds} seconds...")
        time.sleep(sleep_seconds)
    if not booked:
        err.log(
            f"Booking failed after {attempts} attempt" + ("s" if attempts != 1 else "")
        )
        return BookingError.ERROR
    print(
        "Successfully booked class"
        + (f" after {attempts} attempts!" if attempts != 1 else "!")
    )
    if config.notifications:
        ical_url = "not supported"
        notify_booking(config.notifications, _class, ical_url)
    return None


def cancel_fsc_booking(
    auth_session: Session, booking_reference: int, booking_type: BookingType
) -> bool:
    print(f"Cancelling booking of class {booking_reference}")
    res = auth_session.delete(
        f"{booking_url(auth_session)}/{booking_reference}",
        data=json.dumps({"bookingType": booking_type}),
        headers={"Content-Type": "application/json"},
    )
    if res.status_code != requests.codes.OK:
        err.log("Booking cancellation attempt failed: " + res.text)
        return False
    body = res.json()
    if body["success"] is False:
        err.log("Booking cancellation attempt failed: " + body.errorMessage)
        return False
    return True


def try_cancel_fsc_booking(
    integration_user: IntegrationUser, _class: RezervoClass, config: ConfigValue
) -> Union[None, BookingError, AuthenticationError]:
    if config.booking.max_attempts < 1:
        err.log("Max booking cancellation attempts should be a positive number")
        return BookingError.INVALID_CONFIG
    print("Authenticating...")
    auth_session = authenticate_session(
        integration_user.username, integration_user.password
    )
    if isinstance(auth_session, AuthenticationError):
        err.log("Authentication failed")
        return auth_session
    try:
        res = auth_session.get(booking_url(auth_session))
    except requests.exceptions.RequestException as e:
        err.log(
            f"Failed to retrieve sessions for '{integration_user.username}'",
            e,
        )
        return BookingError.ERROR
    bookings_response: BookingsResponse = res.json()
    booking_id = None
    booking_type = None
    for booking in bookings_response["data"]:
        if booking["groupActivity"]["id"] == _class.id:
            booking_type = booking["type"]
            booking_id = booking[booking_type]["id"]
            break
    if booking_id is None or booking_type is None:
        err.log(
            f"No sessions active matching the cancellation criteria for class '{_class.id}'",
        )
        return BookingError.CLASS_MISSING
    cancelled = False
    attempts = 0
    while not cancelled:
        cancelled = cancel_fsc_booking(auth_session, booking_id, booking_type)
        attempts += 1
        if cancelled:
            break
        if attempts >= config.booking.max_attempts:
            break
        sleep_seconds = 2**attempts
        print(f"Exponential backoff, retrying in {sleep_seconds} seconds...")
        time.sleep(sleep_seconds)
    if not cancelled:
        err.log(
            f"Booking cancellation failed after {attempts} attempt"
            + ("s" if attempts != 1 else "")
        )
        return BookingError.ERROR
    print(
        "Successfully cancelled booking"
        + (f" after {attempts} attempts!" if attempts != 1 else "!")
    )
    return None
