import asyncio
import datetime as dt
import json
import sqlite3
from cogs.utils import db
import discord
from discord.ext import commands, tasks
import traceback, sys
from constants import ZERO_WIDTH_CHAR

async def get_guild_data(guild_id):
    data = await db.get_one_data(
        "SELECT \
            guild_id, memechannel_id, memeresultchannel_id, \
            meme_winner_role_id, last_scan \
        FROM guild_info\
        WHERE guild_id=?",
        (guild_id, ))
    return data

async def react_to_message(message):
    try:
        await message.add_reaction("\U0001f44d")
    except discord.errors.NotFound:
        print("Message was deleted before we could react!")

async def get_reaction_results(messages, emoji):
    """
        When given a list of :Class: Message and an emoji, 
        will return a list of messages with the most emoji reactions
    """

    # start reaction count at 2 because the bot should have reacted once
    # and we only want to count messages that have had at least 1 human 
    # react to them 1(bot) + 1(human) = 2
    max_reactions = 2

    results = []

    for message in messages:
        for reaction in message.reactions:
            if reaction.emoji != emoji:
                continue

            if reaction.count == max_reactions:
                results.append(message)

            if reaction.count > max_reactions:
                results = [message]
                max_reactions = reaction.count

    return results, max_reactions - 1

class Memevoting(commands.Cog):

    def __init__(self, bot):

        self.bot = bot
        self.name = "Memevoting"

        self.guild_ids = []

        self.current_scan = dt.datetime.now(tz=dt.timezone.utc)
        self.meme_contest_bg_task.start()


    @commands.Cog.listener()
    async def on_ready(self):
        # Cache all guild_ids the bot is in
        guild_id_tuples = await db.get_all_data(
            "SELECT guild_id FROM guild_info",
            ())

        for guild_id_tuple in guild_id_tuples:
            self.guild_ids.append(guild_id_tuple["guild_id"])

        # React to messages that have been sent since last meme contest
        # in the meme channel of each guild
        for guild_id in self.guild_ids:
            guild_data = await get_guild_data(guild_id)
            memechannel = self.bot.get_channel(guild_data["memechannel_id"])
            last_scan = dt.datetime.fromisoformat(guild_data["last_scan"])
            messages = await memechannel.history(after=last_scan).flatten()
            for message in messages:
                if not message.author == self.bot.user:
                    await react_to_message(message)


    @tasks.loop(seconds=60)
    async def meme_contest_bg_task(self):
        self.current_scan = dt.datetime.now(tz=dt.timezone.utc)
        for guild_id in self.guild_ids:
            last_scan_iso = (await db.get_one_data(
                "SELECT last_scan FROM guild_info WHERE guild_id=?",
                (guild_id,)))["last_scan"]

            last_scan = dt.datetime.fromisoformat(last_scan_iso)

            time_since_last_scan = self.current_scan - last_scan

            
            if dt.timedelta(days=2) < time_since_last_scan < dt.timedelta(days=7):
                await self.remove_meme_role(guild_id)

            if (time_since_last_scan) > dt.timedelta(7):
                print("Scanning... ", time_since_last_scan)
                await self.get_meme_contest_results(guild_id)
                await db.set_data(
                    "UPDATE guild_info SET last_scan=? WHERE guild_id=?",
                    (dt.datetime.isoformat(self.current_scan), guild_id))

    @meme_contest_bg_task.before_loop
    async def before_meme_contest_bg_task(self):
        await self.bot.wait_until_ready()


    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.author.bot or not 
            isinstance(message.channel, discord.abc.GuildChannel)):
            # do nothing if we detect the bot's message, 
            # or message wasnt in a guild.
            return

        # We would like to react to the message with a thumbs up if
        #  message was sent in that guild's meme channel

        # TODO: guild_data should be cached somewhere
        # TODO: and updated if values change
        guild_data = (await get_guild_data(message.guild.id))
        if message.channel.id == guild_data["memechannel_id"]:
            await react_to_message(message)

    async def get_winner_embed(self, participant_msg):
        """
            Takes in a message and the emoji it was measured by,
            and returns a neat embed for the bot to send to the
            results channel.
        """

        head_title = "\U0001f923 This week's UlTiMaTe memes! \U0001f923"
        congrats_message = "Sent by memelord: "

        embed = discord.Embed(title=head_title, colour=discord.Colour(0x4a90e2),
                              timestamp=dt.datetime.now(tz=dt.timezone.utc))
        embed.set_thumbnail(url=participant_msg.author.avatar_url)
        embed.set_footer(text="GucciBot", icon_url=self.bot.user.avatar_url)

        main_content = ""
        if not participant_msg.attachments:
            main_content = participant_msg.content
        else:
            attachment = participant_msg.attachments[0]
            if (
                attachment.filename.endswith(".jpg") or
                attachment.filename.endswith(".jpeg") or
                attachment.filename.endswith(".png")):
                # attachment is an image
                embed.set_image(url=attachment.url)
            
            for attachment in participant_msg.attachments:
                main_content += f"[{attachment.filename}]({attachment.url})\n"

        # Add jump url to the winning message
        embed.add_field(
            name = ZERO_WIDTH_CHAR,
            value = f"**{congrats_message}{participant_msg.author.mention}!**"
                    f"\n**[Link to message]({participant_msg.jump_url})**",
            inline = False
            )

        embed.description = main_content
        return embed


    async def get_meme_contest_results(self, guild_id):
        guild_data = await get_guild_data(guild_id)

        guild = self.bot.get_guild(guild_data["guild_id"])
        meme_channel = guild.get_channel(guild_data["memechannel_id"])
        result_channel = guild.get_channel(guild_data["memeresultchannel_id"])
        meme_winner_role = guild.get_role(guild_data["meme_winner_role_id"])
        last_scan = dt.datetime.fromisoformat(guild_data["last_scan"])

        messages = await meme_channel.history(after=last_scan).flatten()

        if not (messages and result_channel):
            return

        winners_messages, votes = await get_reaction_results(messages, "\U0001f44d")

        for winners_message in winners_messages:
            embed = await self.get_winner_embed(winners_message)
            await result_channel.send(
                content=f"**\U0001f44d {votes}**",
                embed=embed
            )
            member = winners_message.author

            # Give the winner their role :)
            if not meme_winner_role:
                return

            try:
                await member.add_roles(meme_winner_role, reason="meme contest")
            except discord.Forbidden as e:
                print("Bot does not have permission to add these roles.")
            except discord.HTTPException as e:
                print("Unable to add roles!")

    async def remove_meme_role(self, guild_id):

        guild = self.bot.get_guild(guild_id)

        meme_winner_role_id = (await db.get_one_data(
            "SELECT meme_winner_role_id FROM guild_info WHERE guild_id=?",
            (guild_id,)))["meme_winner_role_id"]
        meme_winner_role = guild.get_role(meme_winner_role_id)

        memechannel_id = (await db.get_one_data(
            "SELECT memechannel_id FROM guild_info WHERE guild_id=?",
            (guild_id,)))["memechannel_id"]
        memechannel = guild.get_channel(memechannel_id)

        if not (meme_winner_role or memechannel):
            return

        for member in memechannel.members:
            if not meme_winner_role in member.roles:
                continue

            try:
                await member.remove_roles(meme_winner_role, reason="Meme contest")
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass


def setup(bot):
    bot.add_cog(Memevoting(bot))
