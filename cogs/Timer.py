import asyncio
import datetime

from gtts import gTTS
from discord.ext import commands

from cogs.utils import utils


class Timer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Timer"
        self.bg_task = self.bot.loop.create_task(self.timer_bg_task())

    async def timer_bg_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            current_time = datetime.datetime.now()
            if (current_time.hour == 16 or current_time.hour == 4) and current_time.minute == 20:
                for guild in self.bot.guilds:
                    for voice_channel in guild.voice_channels:
                        if len(voice_channel.members) > 0:
                            # myobj = gTTS(text="Oh look, it's that time again! 4:20 Blaze it!")
                            # myobj.save("420.mp3")
                            await utils.play_file("420.mp3", channel=voice_channel)
                            await asyncio.sleep(0.4)
                            await utils.play_file("sounds/air horn.mp3", channel=voice_channel)
            else:
                pass
            await asyncio.sleep(40)

    # @commands.command()
    # async def backslash(self, ctx):
    #     myobj = gTTS(text="C: BACKSLASH! Users BACKSLASH! I7 4790k BACKSLASH! Desktop BACKSLASH! Workspace BACKSLASH! GucciBot BACKSLASH! venv BACKSLASH! lib BACKSLASH! site-packages BACKSLASH! websockets BACKSLASH! protocol.py BACKSLASH!", lang="fr")
    #     myobj.save("backslash.mp3")
    #     await utils.play_file("backslash.mp3", message=ctx)
    #     # await utils.play_file("timerTTS.mp3", message=ctx)


def setup(bot):
    bot.add_cog(Timer(bot))
