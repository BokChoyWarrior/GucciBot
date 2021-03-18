import traceback
from datetime import datetime
from discord.ext import commands
import discord
import logging
import config
import shutil
from pretty_help import PrettyHelp
from constants import EMBED_COLOUR



# from cogs.utils import db

# check for ffmpeg
def check_for_software(software):
    software_ver = shutil.which(software)
    if software_ver is None:
        print(f"{software} not found - please ensure it is installed within the venv AND/OR the system+path")
    else:
        print(f"{software} found: " + str(software_ver))


check_for_software("ffmpeg")
check_for_software("espeak")

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='GucciBot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.all()
intents.presences = False

prefix = config.prefix
bot = commands.Bot(command_prefix=prefix, description="Welcome to GucciBot!\nCommands are below:",
                   case_insensitive=True, intents=intents)

# help command setup from PrettyHelp
bot.help_command = PrettyHelp(active_time=120.0, color=EMBED_COLOUR)
# bot.help_command = commands.DefaultHelpCommand()
initial_extensions = [
    # 'Fun',
    # 'Audio',
    # "Basics",
    # "Replies",
    # "Memevoting",
    # "MyCaptionBot",
    # "Timer",
    # "Configs",
    "Birthday",
    # "ImageTools",

    "CommandErrorHandler",
    # "Basics2"
]

# class MyHelpCommand(commands.MinimalHelpCommand):
#     async def send_pages(self):
#         destination = self.get_destination()
#         e = discord.Embed(color=discord.Color.blurple(), description='')
#         for page in self.paginator.pages:
#             e.description += page
#         await destination.send(embed=e)

# bot.help_command = MyHelpCommand()
# bot.remove_command('help')

# # My sample help command:
# @bot.command()
# async def help(ctx, args=None):
#     help_embed = discord.Embed(title="My Bot's Help!")
#     command_names_list = [x.name for x in bot.commands]

#     # If there are no arguments, just list the commands:
#     if not args:
#         help_embed.add_field(
#             name="List of supported commands:",
#             value="\n".join([str(i+1)+". "+x.name for i,x in enumerate(bot.commands)]),
#             inline=False
#         )
#         help_embed.add_field(
#             name="Details",
#             value="Type `.help <command name>` for more details about each command.",
#             inline=False
#         )

#     # If the argument is a command, get the help text from that command:
#     elif args in command_names_list:
#         help_embed.add_field(
#             name=args,
#             value=bot.get_command(args).help
#         )

#     # If someone is just trolling:
#     else:
#         help_embed.add_field(
#             name="Nope.",
#             value="Don't think I got that command, boss!"
#         )

#     await ctx.send(embed=help_embed)

@bot.event
async def on_ready():
    print("Everything's all ready to go~")
    print(f'Logged in as: {bot.user.name} with id: {bot.user.id}')
    print('-' * 50)
    await bot.change_presence(activity=discord.Activity(type=2, name='the pigeons'))
    bot.uptime = datetime.now()

@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send('This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send('Sorry. This command is disabled and cannot be used.')

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
