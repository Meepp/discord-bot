from datetime import datetime

from discord import Message, Member, Guild, User


# class Trigger(Base):
#     __tablename__ = 'triggers'
#     __table_args__ = {'extend_existing': True}
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#
#     guild_id = Column('guild_id', String)
#     author = Column('creator', String)
#     author_id = Column('creator_id', String)
#
#     trigger = Column('trigger', String)
#     response = Column('response', String)
#
#     def __init__(self, message: Message):
#         self.guild_id = message.guild.id
#         self.author_id = message.author.id
#         self.author = message.author.name
#
#     def __repr__(self):
#         return "%s -> %s by %s (%s)" % (self.trigger, self.response, self.author, self.guild_id)


class Report:
    def __init__(self, guild: Guild, reportee: Member, reporting: Member):
        self.guild_id = guild.id

        self.reportee = reportee.name
        self.reportee_id = reportee.id

        self.reporting = reporting.name
        self.reporting_id = reporting.id

        self.time = datetime.now()

    def to_mongodb(self):
        return {
            "guild_id": self.guild_id,
            "reportee": self.reportee,
            "reportee_id": self.reportee_id,
            "reporting": self.reporting,
            "reporting_id": self.reporting_id,
            "time": self.time
        }


class Honor:
    def __init__(self, guild: Guild, honoree: User, honoring: User):
        self.guild_id = guild.id

        self.honoree = honoree.name
        self.honoree_id = honoree.id

        self.honoring = honoring.name
        self.honoring_id = honoring.id

        self.time = datetime.now()

    def to_mongodb(self):
        return {
            "guild_id": self.guild_id,
            "honoree": self.honoree,
            "honoree_id": self.honoree_id,
            "honoring": self.honoring,
            "honoring_id": self.honoring_id,
            "time": self.time
        }


# class Song(Base):
#     __tablename__ = 'song'
#     __table_args__ = {'extend_existing': True}
#     id = Column(Integer, primary_key=True, autoincrement=True)
#
#     UniqueConstraint("owner_id", "url")
#
#     owner = Column('owner', String)
#     owner_id = Column('owner_id', String)
#
#     title = Column('title', String)
#     url = Column('url', String)
#     file = Column('file', String)
#
#     latest_playtime = Column('latest_playtime', DateTime)
#
#     def __init__(self, owner: Member, title: str, url: str):
#         self.owner = owner.name
#         self.owner_id = owner.id
#
#         self.title = title
#         self.url = url
#         self.latest_playtime = datetime.now()


class Profile:
    def __init__(self, owner: User):
        self.discord_username = owner.name
        self.discord_id = owner.id
        self.league_user_id = None
        self.balance = 0

    def init_balance(self, user):
        from database.repository import honor_repository

        # Set initial balance to honor count
        count = honor_repository.get_honor_count(user)
        self.balance = count * 100

    def to_mongodb(self):
        return {
            "owner": self.discord_username,
            "owner_id": self.discord_id,
            "league_user_id": self.league_user_id,
            "balance": self.balance,
        }

# class LeagueGame(Base):
#     __tablename__ = 'game'
#     __table_args__ = {'extend_existing': True}
#     id = Column(Integer, primary_key=True, autoincrement=True)
#
#     UniqueConstraint("owner_id", "type")
#
#     channel_id = Column("channel_id", Integer)
#     owner_id = Column('owner_id', String)
#
#     game_id = Column('game_id', String)
#     bet = Column('bet', Integer)
#     team = Column('team', Integer)
#     type = Column('type', String)
#
#     def __init__(self, owner: User):
#         self.owner_id = owner.id


# class RoomModel(Base):
#     """
#     Stores information about a room in which poker games are being played
#     """
#     __tablename__ = "room"
#     __table_args__ = {'extend_existing': True}
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(), nullable=False)
#
#     author = Column(String())
#     author_id = Column(Integer(), nullable=False)
#
#     message_id = Column(Integer())
#
#     created = Column(DateTime(), nullable=False, default=datetime.now())
#     type = Column(String(), nullable=False)
#
#     def __init__(self, name: str, profile: Profile, room_type: str):
#         self.name = name
#         self.author_id = profile.discord_id
#         self.author = profile.discord_username
#         self.type = room_type
