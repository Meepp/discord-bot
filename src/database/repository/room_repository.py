from typing import List, Optional

from database import mongodb as db
from database.models.models import RoomModel


def get_rooms() -> List[RoomModel]:
    session = db.session()

    return session.query(RoomModel).all()


def get_room(room_id: int) -> RoomModel:
    session = db.session()
    return session.query(RoomModel).filter(RoomModel.id == room_id).one_or_none()


def find_room_by_message_id(message_id: int) -> Optional[RoomModel]:
    session = db.session()
    return session.query(RoomModel).filter(RoomModel.message_id == message_id).one_or_none()
