from datetime import datetime

from discord import Message, Member, Guild, User
from sqlalchemy import Integer, Column, String, DateTime, UniqueConstraint, ForeignKey

from database import Base


class Trigger(Base):
    __tablename__ = 'triggers'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)

    guild_id = Column('guild_id', String)
    author = Column('creator', String)
    author_id = Column('creator_id', String)

    trigger = Column('trigger', String)
    response = Column('response', String)

    def __init__(self, message: Message):
        self.guild_id = message.guild.id
        self.author_id = message.author.id
        self.author = message.author.name

    def __repr__(self):
        return "%s -> %s by %s (%s)" % (self.trigger, self.response, self.author, self.guild_id)


class Report(Base):
    __tablename__ = 'report'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)

    guild_id = Column('guild_id', String)
    reportee = Column('reportee', String)
    reportee_id = Column('reportee_id', String)

    reporting = Column('reporting', String)
    reporting_id = Column('reporting_id', String)

    time = Column('time', DateTime)

    def __init__(self, guild: Guild, reportee: Member, reporting: Member):
        self.guild_id = guild.id

        self.reportee = reportee.name
        self.reportee_id = reportee.id

        self.reporting = reporting.name
        self.reporting_id = reporting.id

        self.time = datetime.now()


class Honor(Base):
    __tablename__ = 'honor'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)

    guild_id = Column('guild_id', String)
    honoree = Column('honoree', String)
    honoree_id = Column('honoree_id', String)

    honoring = Column('honoring', String)
    honoring_id = Column('honoring_id', String)

    time = Column('time', DateTime)

    def __init__(self, guild: Guild, honoree: User, honoring: User):
        self.guild_id = guild.id

        self.honoree = honoree.name
        self.honoree_id = honoree.id

        self.honoring = honoring.name
        self.honoring_id = honoring.id

        self.time = datetime.now()


class Song(Base):
    __tablename__ = 'song'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)

    UniqueConstraint("owner_id", "url")

    owner = Column('owner', String)
    owner_id = Column('owner_id', String)

    title = Column('title', String)
    url = Column('url', String)
    file = Column('file', String)

    latest_playtime = Column('latest_playtime', DateTime)

    def __init__(self, owner: Member, title: str, url: str):
        self.owner = owner.name
        self.owner_id = owner.id

        self.title = title
        self.url = url
        self.latest_playtime = datetime.now()


class Profile(Base):
    __tablename__ = 'profile'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)

    discord_username = Column('owner', String)
    discord_id = Column('owner_id', Integer, unique=True)

    balance = Column('balance', Integer, default=0)

    league_user_id = Column('league_user_id', String)

    def __init__(self, owner: User):
        self.discord_username = owner.name
        self.discord_id = owner.id

    def init_balance(self, session, user):
        from database.repository import honor_repository

        # Set initial balance to honor count
        count = honor_repository.get_honor_count(user)
        self.balance = count * 100
        session.commit()


class LeagueGame(Base):
    __tablename__ = 'game'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)

    UniqueConstraint("owner_id", "type")

    channel_id = Column("channel_id", Integer)
    owner_id = Column('owner_id', String)

    game_id = Column('game_id', String)
    bet = Column('bet', Integer)
    team = Column('team', Integer)
    type = Column('type', String)

    def __init__(self, owner: User):
        self.owner_id = owner.id


class RoomModel(Base):
    """
    Stores information about a room in which poker games are being played
    """
    __tablename__ = "room"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(), nullable=False)

    author = Column(String())
    author_id = Column(Integer(), nullable=False)

    message_id = Column(Integer())

    created = Column(DateTime(), nullable=False, default=datetime.now())
    type = Column(String(), nullable=False)

    def __init__(self, name: str, profile: Profile, room_type: str):
        self.name = name
        self.author_id = profile.discord_id
        self.author = profile.discord_username
        self.type = room_type
