from captionbot import CaptionBot
from discord.ext import commands


class MyCaptionBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.c = CaptionBot()

    @commands.command()
    async def caption(self, ctx, url_query):
        if ctx.channel.id == 669139299350085662:
            caption = self.c.url_caption(str(url_query))
            await ctx.send(caption)


def setup(bot):
    bot.add_cog(MyCaptionBot(bot))