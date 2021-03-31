import time
import discord
from discord.ext import commands


class Basics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Basics"

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command(name="shutdown", aliases=["s", "sh", "sd", "close", "exit"])
    @commands.guild_only()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Kills the bot."""
        await ctx.message.delete()
        await self.bot.logout()
        await self.bot.close()

    @commands.command(aliases=["p"])
    async def ping(self, ctx):
        """Shows the Gateway Ping."""
        t1 = time.perf_counter()
        await ctx.trigger_typing()
        t2 = time.perf_counter()
        await ctx.send(f":hourglass: gateway ping: {round((t2 - t1) * 1000)}ms :hourglass:")


    @commands.command(name="repeat", aliases=["reply", "emoji"])
    async def repeat(self, ctx, *, args):
        """Repeats the message you sent back to you, in a code block."""
        await ctx.send(f"```{args}```")
    # @commands.command()
    # @commands.is_owner()
    # async def setpresence(self, ctx, *, content):
    #     """Changing bots presence"""
    #     if len(content) > 0:
    #         await self.bot.change_presence(activity=discord.Game(name=content))
    #         await ctx.send("Presence sucesfully changed to\n ```" + content + "```")
    #     else:
    #         await ctx.send("Presence cannot be empty string")


def setup(bot):
    bot.add_cog(Basics(bot))
