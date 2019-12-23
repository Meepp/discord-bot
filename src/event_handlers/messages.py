from src import bot


@bot.client.event
async def on_message(message):
    if message.guild not in bot.triggers:
        bot.update_triggers(message)

    if message.content.startswith("!"):
        msg_array = message.content.split(" ")

        if len(msg_array) == 0:
            return

        cmd = msg_array[0][1:]
        args = msg_array[1:]
        if cmd in bot.commands:
            await bot.commands[cmd](args, message)
    else:
        if message.author.bot:
            return

        for trigger in bot.triggers[message.guild]:
            if trigger.trigger in message.content:
                await message.channel.send(trigger.response)
