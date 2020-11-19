from datetime import datetime

from discord import Message, Member, Guild
from sqlalchemy import Integer, Column, String, DateTime, UniqueConstraint

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

    def __init__(self, guild: Guild, honoree: Member, honoring: Member):
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

