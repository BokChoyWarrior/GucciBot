import asyncio
from discord.ext import commands
from cogs.utils import utils

class Configs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Configs"

    async def handle_input(self, ctx, text):
        try:
            channel_id = int(text)
        except ValueError:
            await ctx.send("Please enter a valid channel ID")
            return

        if not utils.channel_exists(channel_id, ctx.guild):
            await ctx.send("Channel with ID \"" + str(channel_id) + "\" doesn't exist in this guild.")
            return
        return channel_id

    @commands.command()
    async def serious(self, ctx, text):
        channel_id = await self.handle_input(ctx, text)
        if not channel_id:
            return
        utils.change_seriousness(channel_id)
        await ctx.send("**<#" + str(channel_id) + ">** with ID " + str(channel_id) + " had it's serious level changed.")

    @commands.command()
    async def isserious(self, ctx, text):
        channel_id = await self.handle_input(ctx, text)
        if not channel_id:
            return
        reply = ""
        if utils.channel_is_serious(channel_id):
            reply = " is serious - audio will not play there."
        else:
            reply = " is not serious - audio will play there."

        await ctx.send("**<#" + str(channel_id) + ">** (ID " + str(channel_id) + ") " + reply)

def setup(bot):
    bot.add_cog(Configs(bot))
