import asyncio
import discord
from discord.ext import commands
from cogs.utils import utils


async def handle_input(ctx, text):
    """Returns channel_id if the id is valid and exists in ctx.guild"""
    try:
        channel_id = int(text)
    except ValueError:
        await ctx.send("Please enter a valid channel ID")
        return

    if utils.check_channel_existence_and_type(channel_id, ctx.guild) != discord.VoiceChannel:
        await ctx.send("Voice channel with ID \"" + str(channel_id) + "\" doesn't exist in this guild.")
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
        """Changes a channel's serious setting. If a channel is serious, the bot will not join that particular voice
        channel. """
        channel_id = await handle_input(ctx, text)
        if not channel_id:
            return
        serious = utils.change_seriousness(ctx, channel_id)
        if not serious:
            srs_string = "not "
        else:
            srs_string = ""
        await ctx.send("**<#" + str(channel_id) + ">** with ID " + str(channel_id)
                       + f" had it's serious level changed and is now **{srs_string}serious**.")

    @commands.command(usage="""channel_id
    Where channel_id is an id of a voice channel in your server.""")
    @commands.guild_only()
    async def isserious(self, ctx, text):
        """Checks a voice channel's serious level. (Whether or not the bot can use voice in the channel)"""
        channel_id = await handle_input(ctx, text)
        if not channel_id:
            return
        if utils.channel_is_serious(str(ctx.guild.id), str(channel_id)):
            reply = " is serious - audio will not play there."
        else:
            reply = " is not serious - audio will play there."

        await ctx.send("**<#" + str(channel_id) + ">** (ID " + str(channel_id) + ") " + reply)

    @commands.command()
    @commands.guild_only()
    async def listserious(self, ctx):
        serious_channels = utils.get_serious_channel_data()[str(ctx.guild.id)]
        print(serious_channels)
        reply = "**Serious voice channels in this server:**\n"
        for serious_channel in serious_channels:
            reply += f"<#{serious_channel}>\n"
        await ctx.send(reply)


def setup(bot):
    bot.add_cog(Configs(bot))
