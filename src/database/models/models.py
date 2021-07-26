from datetime import datetime

from discord import Message, Member, Guild, User


class Trigger:
    def __init__(self, message: Message, trig, resp):
        self.guild_id = str(message.guild.id) # String to make consistent with previous model scheme
        self.creator_id = str(message.author.id)
        self.creator = message.author.name
        self.trigger = trig
        self.response = resp

    def to_mongodb(self):
        return {
            "guild_id": self.guild_id,
            "creator_id": self.creator_id,
            "creator": self.creator,
            "trigger": self.trigger,
            "response": self.response
        }

    def __repr__(self):
        return "%s -> %s by %s (%s)" % (self.trigger, self.response, self.author, self.guild_id)


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


class Song:
    def __init__(self, owner: Member, title: str, url: str):
        self.owner = owner.name
        self.owner_id = owner.id

        self.title = title
        self.url = url
        self.latest_playtime = datetime.now()

    def to_mongodb(self):
        return {
            "owner": self.owner,
            "owner_id": self.owner_id,
            "title": self.title,
            "url": self.url,
            "latest_playtime": self.latest_playtime
        }


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
