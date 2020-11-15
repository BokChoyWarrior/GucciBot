import random

from discord import Role

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

    """ AOE2 sounds """
    @commands.group()
    async def aoe2(self, ctx):
        pass

    @aoe2.group(name="11")
    async def _11(self, ctx):
        await utils.play_file("sounds/aoe2/11.ogg", ctx)

    @aoe2.group(name="12")
    async def _12(self, ctx):
        await utils.play_file("sounds/aoe2/12.ogg", ctx)

    @aoe2.group(name="13")
    async def _13(self, ctx):
        await utils.play_file("sounds/aoe2/13.ogg", ctx)

    @aoe2.group(name="14")
    async def _14(self, ctx):
        await utils.play_file("sounds/aoe2/14.ogg", ctx)

    @aoe2.group(name="30")
    async def _30(self, ctx):
        await utils.play_file("sounds/aoe2/30.ogg", ctx)

    """ PLAY commands"""
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

    @play.group(name="1201")
    async def _1201(self, ctx):
        await utils.play_file("sounds/1201.mp3", ctx)

    @play.group(name="1811")
    async def _1811(self, ctx):
        await utils.play_file("sounds/stop inviting me to dota.mp3", ctx)

    @play.group(name="btc")
    async def _btc(self, ctx):
        btc = random.randint(0, 41)
        sound_path = f"sounds/bitconnect/Bitconnect{btc}.mp3"
        await utils.play_file(sound_path, ctx)


def setup(bot):
    bot.add_cog(Audio(bot))
