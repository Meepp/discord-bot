import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


class Database:
    def __init__(self, name: str):
        self.engine = sqlalchemy.create_engine('sqlite:///' + name, echo=False)
        self.connection = self.engine.connect()
        self._session_factory = sessionmaker(autocommit=False, autoflush=True, bind=self.engine)
        self._session = scoped_session(self._session_factory)

    def session(self) -> scoped_session:
        return self._session()


# Create db
Base = declarative_base()
db = Database("database.db")

