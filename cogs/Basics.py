import time

import discord
from discord.ext import commands
from discord.ext.commands import bot


class Basics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Basics"

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Ready for {self.name}!")

    @commands.command(name="shutdown", aliases=["s", "sh", "sd", "close", "exit"])
    @commands.guild_only()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Kills the bot."""
        await ctx.send("You're such a turnoff")
        await self.bot.logout()
        await self.bot.close()

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Shows the Gateway Ping."""
        t1 = time.perf_counter()
        await ctx.trigger_typing()
        t2 = time.perf_counter()
        await ctx.send(f":hourglass: gateway ping: {round((t2 - t1) * 1000)}ms :hourglass:")

    @commands.command()
    @commands.is_owner()
    async def setpresence(self, ctx, *, content):
        """Changing bots presence"""
        if len(content) > 0:
            await self.bot.change_presence(activity=discord.Game(name=content))
            await ctx.send("Presence sucesfully changed to\n ```" + content + "```")
        else:
            await ctx.send("Presence cannot be empty string")

    @commands.command()
    async def stop(self, ctx):
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()


def setup(bot):
    bot.add_cog(Basics(bot))