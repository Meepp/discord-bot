from datetime import datetime

from discord import Message, Member, Guild, User

class Trigger:
    def __init__(self, message: Message, trig, resp):
        self.guild_id = message.guild.id
        self.creator_id = message.author.id
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
        return "%s -> %s by %s (%s)" % (self.trigger, self.response, self.creator, self.guild_id)


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


class Playlist(Base):
    __tablename__ = "playlist"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)

    title = Column('title', String)

    owner_id = Column('owner_id', String)

    public = Column('public', Boolean, default=True)

    def __init__(self, owner: Member, title: str):
        self.owner_id = owner.id

        self.title = title


class PlaylistSong(Base):
    __tablename__ = "playlist_song"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)

    playlist_id = Column('playlist_id', String, ForeignKey("playlist.id"))
    playlist = relationship('src.database.models.models.Playlist')

    song_id = Column('song_id', String, ForeignKey("song.id"))
    song = relationship('src.database.models.models.Song')

    def __init__(self, playlist: Playlist, song: Song):
        self.playlist_id = playlist.id
        self.song_id = song.id


class Profile(Base):
    def __init__(self, owner: User):
        self.discord_username = owner.name
        self.discord_id = owner.id
        self.league_user_id = None
        self.balance = 0
        self.active_playlist = None

    def init_balance(self):
        from database.repository import honor_repository

        # Set initial balance to honor count
        count = honor_repository.get_honor_count_by_id(self.discord_id)
        self.balance = count * 100

    def to_mongodb(self):
        return {
            "owner": self.discord_username,
            "owner_id": self.discord_id,
            "league_user_id": self.league_user_id,
            "balance": self.balance,
        }


class LeagueGame:
    def __init__(self, owner: User, amount, type, channel_id):
        self.owner_id = owner.id
        self.amount = amount
        self.type = type
        self.channel_id = channel_id
        self.game_id = None
        self.team = None

    def to_mongodb(self):
        return {
            "owner_id": self.owner_id,
            "amount": self.amount,
            "type": self.type,
            "channel_id": self.channel_id,
            "game_id": self.game_id,
            "team": self.team
        }


class EsportGame:
    def __init__(self, owner: User, match_id, amount, team, channel_id):
        self.owner_id = owner.id
        self.game_id = match_id
        self.amount = amount
        self.team = team
        self.odds = 1
        self.channel_id = channel_id

    def to_mongodb(self):
        return {
            "owner_id": self.owner_id,
            "game_id": self.game_id,
            "amount": self.amount,
            "team": self.team,
            "odds": self.odds,
            "channel_id": self.channel_id,
        }


class RoomModel:
    """
    Stores information about a room in which poker games are being played
    """

    def __init__(self, name: str, profile: dict, room_type: str, created, message_id):
        self.name = name
        self.author_id = profile['owner_id']
        self.author = profile['owner']
        self.type = room_type
        self.created = created
        self.message_id = message_id

    def to_mongodb(self):
        return {
            "name": self.name,
            "author_id": self.author_id,
            "author": self.author,
            "type": self.type,
            "created": self.created,
            "message_id": self.message_id
        }
