from captionbot import CaptionBot
from discord.ext import commands
from .utils.utils import measure_time


class MyCaptionBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.c = CaptionBot()

    @commands.command()
    async def caption(self, ctx, url_query):
        print("Captioning: " + url_query)
        with measure_time("Getting caption from MS"):
            caption = self.c.url_caption(str(url_query))
        await ctx.send(caption)


def setup(bot):
    bot.add_cog(MyCaptionBot(bot))
