import asyncio
from discord.ext import commands
from cogs.utils import utils


async def handle_input(ctx, text):
    try:
        channel_id = int(text)
    except ValueError:
        await ctx.send("Please enter a valid channel ID")
        return

    if not utils.channel_exists(channel_id, ctx.guild):
        await ctx.send("Channel with ID \"" + str(channel_id) + "\" doesn't exist in this guild.")
        return
    return channel_id


class Configs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Configs"

    @commands.command(usage="""channel_id
    Where channel_id is an id of a voice channel in your server.""")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_permissions=True)
    async def serious(self, ctx, text):
        """Changes a channel's serious setting. If a channel is serious, the bot will not join that particular voice channel."""
        channel_id = await handle_input(ctx, text)
        if not channel_id:
            return
        serious = utils.change_seriousness(channel_id)
        if not serious:
            srs_string = "not "
        else:
            srs_string = ""
        await ctx.send("**<#" + str(channel_id) + ">** with ID " + str(channel_id) + f" had it's serious level changed and is now **{srs_string}serious**.")

    @commands.command(usage="""channel_id
    Where channel_id is an id of a voice channel in your server.""")
    @commands.guild_only()
    async def isserious(self, ctx, text):
        """Checks a voice channel's serious level. (Whether or not the bot can use voice in the channel)"""
        channel_id = await handle_input(ctx, text)
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
