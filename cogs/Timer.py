import asyncio
import datetime

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
                            await utils.play_files(
                                [
                                    "sounds/420.mp3",
                                    "sounds/smoke_weed_everyday.mp3",
                                    "sounds/air horn.mp3"
                                ],
                                voice_channel
                            )
                await asyncio.sleep(3600)
            await asyncio.sleep(5)


def setup(bot):
    bot.add_cog(Timer(bot))
