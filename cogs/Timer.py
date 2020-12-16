import asyncio
import datetime
import os.path

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
            current_time = datetime.datetime.utcnow()
            if (current_time.hour == 16 or current_time.hour == 4) and current_time.minute == 20:
                for guild in self.bot.guilds:
                    for voice_channel in guild.voice_channels:
                        if len(voice_channel.members) > 0:
                            if not os.path.isfile("420.mp3"):
                                myobj = gTTS(text="Oh look, it's that time again! 4:20 Blaze it!", lang="en")
                                myobj.save("420.mp3")
                            await utils.play_files(["420.mp3", "sounds/air horn.mp3"], channel=voice_channel)
                await asyncio.sleep(3600)
            await asyncio.sleep(5)


def setup(bot):
    bot.add_cog(Timer(bot))
