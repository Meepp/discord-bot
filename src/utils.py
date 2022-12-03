import asyncio
import functools


def create_table(header, data, function, page=0):
    from src import bot
    ret = "```%s\n" % header

    start = page * bot.settings.page_size
    end = start + bot.settings.page_size
    for i, row in enumerate(data[start:end]):
        ret += function(i, row) + "\n"

    return ret + "```"


def run_in_executor(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, functools.partial(f, *args, **kwargs))

    return inner
