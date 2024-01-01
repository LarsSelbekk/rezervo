from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

from rezervo.api.common import get_db, token_auth_scheme
from rezervo.chains.common import (
    book_class,
    cancel_booking,
    find_authed_class_by_id,
)
from rezervo.database import crud
from rezervo.errors import AuthenticationError, BookingError
from rezervo.schemas.config.config import ConfigValue
from rezervo.schemas.config.user import ChainIdentifier, ChainUser
from rezervo.sessions import pull_sessions
from rezervo.settings import Settings, get_settings
from rezervo.utils.logging_utils import err

router = APIRouter()


def authenticate_chain_user_with_config(
    chain_identifier: ChainIdentifier,
    db: Session,
    settings: Settings,
    token: str,
) -> tuple[ChainUser, ConfigValue]:
    db_user = crud.user_from_token(db, settings, token)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    chain_user = crud.get_chain_user(db, chain_identifier, db_user.id)
    if chain_user is None:
        err.log(f"No '{chain_identifier}' user for given user id")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return chain_user, crud.get_user_config(db, db_user).config


class BookingPayload(BaseModel):
    class_id: str


@router.post("/{chain_identifier}/book")
def book_class_api(
    chain_identifier: ChainIdentifier,
    payload: BookingPayload,
    token=Depends(token_auth_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    print("Authenticating rezervo user...")
    chain_user, config = authenticate_chain_user_with_config(
        chain_identifier, db, settings, token
    )
    print("Searching for class...")
    _class = find_authed_class_by_id(chain_user, config, payload.class_id)
    match _class:
        case AuthenticationError():
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        case BookingError():
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    print("Booking class...")
    booking_result = book_class(chain_user, _class, config)
    match booking_result:
        case AuthenticationError():
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        case BookingError():
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # Pulling in foreground to have sessions up-to-date once the response is sent
    pull_sessions(chain_identifier, chain_user.user_id)


class BookingCancellationPayload(BaseModel):
    class_id: str


@router.post("/{chain_identifier}/cancel-booking")
def cancel_booking_api(
    chain_identifier: ChainIdentifier,
    payload: BookingCancellationPayload,
    token=Depends(token_auth_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    print("Authenticating rezervo user...")
    chain_user, config = authenticate_chain_user_with_config(
        chain_identifier, db, settings, token
    )
    print("Searching for class...")
    _class = find_authed_class_by_id(chain_user, config, payload.class_id)
    match _class:
        case AuthenticationError():
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        case BookingError():
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    print("Cancelling booking...")
    cancellation_res = cancel_booking(chain_user, _class, config)
    match cancellation_res:
        case AuthenticationError():
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        case BookingError():
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # Pulling in foreground to have sessions up-to-date once the response is sent
    pull_sessions(chain_identifier, chain_user.user_id)
