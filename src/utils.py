from src import bot


def create_table(header, data, function, page=0):
    ret = "```%s\n" % header

    start = page * bot.settings.page_size
    end = start + bot.settings.page_size
    for i, row in enumerate(data[start:end]):
        ret += function(i, row) + "\n"

    return ret + "```"
