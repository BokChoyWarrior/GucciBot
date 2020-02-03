import traceback
from datetime import datetime
from discord.ext import commands
import discord
import logging
import config

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='GucciBot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


prefix = config.prefix
bot = commands.Bot(command_prefix=config["prefix"], description="Welcome to PradaBot!\nCommands are below:",
                   case_insensitive=True)

initial_extensions = [
    'Fun',
    'Audio',
    "Basics",
    "Replies",
    "Memevoting",
    "MyCaptionBot"
]


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send('This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send('Sorry. This command is disabled and cannot be used.')


@bot.event
async def on_ready():
    print("Everything's all ready to go~")
    print(f'Logged in as: {bot.user.name} with id: {bot.user.id}')
    print('-' * 50)
    await bot.change_presence(activity=discord.Activity(type=2, name='the pigeons'))
    bot.uptime = datetime.now()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    time = datetime.now().strftime("%I:%M %p")

    print("\nMESSAGE\n-------\n"
          "Content     : {0.content}\n"
          "Author      : {0.author}\n"
          "Text channel: {0.channel}\n"
          "Guild       : {0.guild}\n"
          "Time        : {1}\n".format(message, time))

    await bot.process_commands(message)


@bot.event
async def on_command(ctx):
    pass


if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension("cogs." + extension)
        except Exception as e:
            print(traceback.format_exc())

bot.run(config.token)
