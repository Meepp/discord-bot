import os
import pathlib



def create_directories():
    pathlib.Path("storage").mkdir(parents=True, exist_ok=True)
    pathlib.Path("storage/data").mkdir(parents=True, exist_ok=True)
    pathlib.Path("storage/models").mkdir(parents=True, exist_ok=True)
    print("Created directories")


def main():
    create_directories()
    from src import bot
    bot.run(bot.token)


if __name__ == "__main__":
    main()
