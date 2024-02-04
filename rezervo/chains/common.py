from typing import Union

from rezervo import models
from rezervo.chains.active import get_chain
from rezervo.database.database import SessionLocal
from rezervo.errors import AuthenticationError, BookingError
from rezervo.notify.slack import delete_scheduled_dm_slack, notify_cancellation_slack
from rezervo.providers.schema import LocationIdentifier
from rezervo.schemas.config.config import ConfigValue, Slack
from rezervo.schemas.config.user import (
    ChainIdentifier,
    ChainUser,
    Class,
)
from rezervo.schemas.schedule import RezervoClass, RezervoSchedule
from rezervo.utils.logging_utils import warn


async def find_class_by_id(
    chain_user: ChainUser,
    class_id: str,
) -> Union[RezervoClass, BookingError, AuthenticationError]:
    return await get_chain(chain_user.chain).find_class_by_id(class_id)


async def find_class(
    chain_identifier: ChainIdentifier, _class_config: Class
) -> Union[RezervoClass, BookingError, AuthenticationError]:
    return await get_chain(chain_identifier).find_class(_class_config)


async def book_class(
    chain_user: ChainUser, _class: RezervoClass, config: ConfigValue
) -> Union[None, BookingError, AuthenticationError]:
    return await get_chain(chain_user.chain).try_book_class(chain_user, _class, config)


async def cancel_booking(
    chain_user: ChainUser, _class: RezervoClass, config: ConfigValue
) -> Union[None, BookingError, AuthenticationError]:
    res = await get_chain(chain_user.chain).try_cancel_booking(
        chain_user, _class, config
    )
    if res is None:
        if config.notifications is not None and config.notifications.slack is not None:
            update_slack_notifications_with_cancellation(
                chain_user.chain, _class, config.notifications.slack
            )
        else:
            warn.log(
                "Slack notifications config not specified, no Slack notifications will updated after cancellation!"
            )
    return res


def update_slack_notifications_with_cancellation(
    chain_identifier: ChainIdentifier, _class: RezervoClass, slack_config: Slack
):
    if slack_config.user_id is None:
        return None
    with SessionLocal() as db:
        receipts = (
            db.query(models.SlackClassNotificationReceipt)
            .filter_by(
                class_id=_class.id,
                slack_user_id=slack_config.user_id,
                chain=chain_identifier,
                channel_id=slack_config.channel_id,
            )
            .all()
        )
    for receipt in receipts:
        notify_cancellation_slack(
            slack_config.bot_token, slack_config.channel_id, receipt.message_id
        )
        reminder_id = receipt.scheduled_reminder_id
        if reminder_id is not None:
            delete_scheduled_dm_slack(
                slack_config.bot_token,
                slack_config.user_id,
                reminder_id,
            )
    with SessionLocal() as db:
        for receipt in receipts:
            db.delete(receipt)
        db.commit()


async def fetch_week_schedule(
    chain_identifier: ChainIdentifier,
    week_offset: int,
    locations: list[LocationIdentifier],
) -> RezervoSchedule:
    return await get_chain(chain_identifier).fetch_week_schedule(week_offset, locations)
