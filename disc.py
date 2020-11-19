from src import bot


def main():
    # Import database models
    from src.database import Base, db
    # Setup database models
    Base.metadata.create_all(db.engine)

    bot.run(bot.token)


if __name__ == "__main__":
    main()
