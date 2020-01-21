from .utils import utils
from discord.ext import commands

prefix = "!"


class Audio(commands.Cog, name="Audio"):
    def __init__(self, bot):
        self.bot = bot
        self.name = "Audio"

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    @commands.group()
    async def play(self, ctx):
        pass

    @play.group(name="airhorn")
    async def _Airhorn(self, ctx):
        await utils.play_file("sounds/air horn.mp3", ctx)

    @play.group(name="weed")
    async def _Weed(self, ctx):
        await utils.play_file("sounds/Weed.mp3", ctx)

    @play.group(name="bloodclart")
    async def _bloodclart(self, ctx):
        await utils.play_file("sounds/Blood clart.mp3", ctx)

    @play.group(name="bloodclot")
    async def _bloodclot(self, ctx):
        await utils.play_file("sounds/Bloodclot.mp3", ctx)

    @play.group(name="blood_clot")
    async def _blood_clot(self, ctx):
        await utils.play_file("sounds/Blood clot.mp3", ctx)

    @play.group(name="cummy")
    async def _cummy(self, ctx):
        await utils.play_file("sounds/Can you guy stop making Cummy say weird shit.mp3", ctx)

    @play.group(name="brainless")
    async def _brainless(self, ctx):
        await utils.play_file("sounds/It's incredible how brainless you are.mp3", ctx)


def setup(bot):
    bot.add_cog(Audio(bot))
