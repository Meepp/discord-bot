from typing import List

from database import db
from database.models.models import RoomModel


def get_rooms() -> List[RoomModel]:
    session = db.session()

    return session.query(RoomModel).all()


def get_room(room_id: int) -> RoomModel:
    session = db.session()
    return session.query(RoomModel).filter(RoomModel.id == room_id).one_or_none()
