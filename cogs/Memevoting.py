import asyncio
import datetime as dt
import json
from cogs.utils import db
import discord
from discord.ext import commands


class Memevoting(commands.Cog):

    def __init__(self, bot):
        # Below is a sample of the OLD storage format of the meme channels and such for each guild.
        # This should be migrated to a database at some point...

        # {
        #     "guild_ids": {
        #         "95947555887652864": {
        #             "memechannel_id": 668470137975865344,
        #             "memeresultchannel_id": 779658905021710336,
        #             "meme_winner_role_id": 669282415310798868,
        #             "meme_loser_role_id": 668798124751323146
        #         }
        #     },
        #     "last_scan": "2020-11-20T18:00:00"
        # }


        # SQLite implementation - tuple
        # ( 
        # 0 guild_id:int, 
        # 1 memechannel_id:int or 0, 
        # 2 memeresultchannel_id:int or 0, 
        # 3 meme_winner_role_id:int, 
        # 4 last_scan:string (DateTime iso format)
        # 5 serious_channels:string  "channel_id1 channelid2 chanelid3 " etc
        # )


        self.bot = bot
        self.name = "Memevoting"
        # with open("cogs/cogfigs/Memevoting.json", "r+") as f:
        #     self.data = json.load(f)
        # self.data = db.get_data("SELECT * FROM memevoting", ()) --- not needed?
        self.guild_ids = db.get_data("SELECT guild_id FROM guild_info", ())
        # self.last_scan = dt.datetime.fromisoformat(self.data["last_scan"]) --add fix
        self.current_scan = dt.datetime.utcnow()
        self.bg_task = self.bot.loop.create_task(self.meme_contest_bg_task())

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id_tuple in self.guild_ids:
            guild_data = await self.get_guild_data(guild_id_tuple)
            # memechannel = self.bot.get_channel(self.guild_ids[guild_id]["memechannel_id"])
            memechannel = self.bot.get_channel(guild_data[1])
            last_scan = dt.datetime.fromisoformat(guild_data[4])
            messages = await memechannel.history(after=last_scan).flatten()
            for message in messages:
                if not message.author == self.bot.user:
                    await self.react_to_message(message)

    async def meme_contest_bg_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.current_scan = dt.datetime.utcnow()
            for guild_id_tuple in self.guild_ids:
                guild_id = guild_id_tuple[0]
                last_scan = dt.datetime.fromisoformat(db.get_data("SELECT last_scan FROM guild_info WHERE guild_id=?", guild_id_tuple))
                if dt.timedelta(2) < self.current_scan - last_scan < dt.timedelta(7):
                    await self.remove_meme_roles(guild_id)
                if self.current_scan - last_scan > dt.timedelta(7):
                    print("Scanning... ", self.current_scan - last_scan)
                    await self.get_meme_contest_results(guild_id_tuple)
                    last_scan += dt.timedelta(7)
                    db.set_data("UPDATE guild_info SET last_scan=? WHERE guild_id=?", (dt.datetime.isoformat(last_scan), ) + guild_id_tuple)


            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_message(self, message):
        guild_data = await self.get_guild_data((message.guild.id,))
        if message.author == self.bot.user:
            return
        if message.channel.id == guild_data[1]:
            await self.react_to_message(message)

    async def get_result_embed(self, participant_msg, winner_or_loser, emoji=""):
        if winner_or_loser == "winner":
            head_title = "\U0001f923 This week's UlTiMaTe memes! \U0001f923"
            congrats_message = "Sent by memelord: "
        # elif winner_or_loser == "loser":
        #     head_title = "\U0001F4A9 This week's ShItTeSt memes! \U0001F4A9"
        #     congrats_message = "Sent by boring loser: "

        embed = discord.Embed(title=head_title, colour=discord.Colour(0x4a90e2),
                              timestamp=dt.datetime.now(tz=dt.timezone.utc))
        embed.set_thumbnail(url=participant_msg.author.avatar_url)
        embed.set_footer(text="GucciBot", icon_url=self.bot.user.avatar_url)

        if not participant_msg.attachments:
            main_content = participant_msg.content
        else:
            attachment = participant_msg.attachments[0]
            if (attachment.filename.endswith(".jpg") or attachment.filename.endswith(".jpeg") or
                    attachment.filename.endswith(".png")):
                embed.set_image(url=attachment.url)
            main_content = f"[{attachment.filename}]({attachment.url})"

        embed.add_field(name=f"**{congrats_message}{participant_msg.author.display_name}!**", value=f"**[Link to message]({participant_msg.jump_url})**")

        embed.description = main_content
        return embed

    async def get_meme_contest_results(self, guild_id_tuple):
        guild_data = await self.get_guild_data(guild_id_tuple)

        guild = self.bot.get_guild(guild_data[0])
        memechannel = guild.get_channel(guild_data[1])
        memeresultchannel = guild.get_channel(guild_data[2])
        meme_winner_role = guild.get_role(guild_data[3])
        last_scan = dt.datetime.fromisoformat(guild_data[4])
        messages = await memechannel.history(after=last_scan).flatten()
        if not messages:
            return
        winners_messages, upvotes = await self.get_reaction_results(messages, "\U0001f44d")
        # losers_messages, downvotes = await self.get_reaction_results(messages, "\U0001f44e")


        # TODO: tidy this up!
        # loser_members = []
        # for losers_message in losers_messages:
        #     embed = await self.get_result_embed(losers_message, winner_or_loser="loser", emoji="\U0001f44e")
        #     # await memechannel.send(content=f"**\U0001f44e {downvotes}**", embed=embed)
        #     member = losers_message.author
        #     if member not in loser_members:
        #         loser_members.append(member)
        #         try:
        #             await member.add_roles(meme_loser_role, reason="meme contest")
        #         except discord.Forbidden as e:
        #             print(e + " - You do not have permission to add these roles.")
        #         except discord.HTTPException as e:
        #             print(e)

        for winners_message in winners_messages:
            embed = await self.get_result_embed(winners_message, winner_or_loser="winner", emoji="\U0001f44d")
            if not memeresultchannel is None:  # clean this up
                await memeresultchannel.send(content=f"**\U0001f44d {upvotes}**", embed=embed)
            member = winners_message.author
            # if member in loser_members:  # member can't be winner AND loser!
            try:
                if meme_winner_role:
                    await member.add_roles(meme_winner_role, reason="meme contest")
            except discord.Forbidden as e:
                print("Bot does not have permission to add these roles.")
            except discord.HTTPException as e:
                print("Unable to add roles!")

    async def remove_meme_roles(self, guild_id):
        guild = self.bot.get_guild(guild_id)
        
        meme_winner_role = guild.get_role(db.get_data("SELECT meme_winner_role_id FROM guild_info WHERE guild_id=?", (guild_id,)))
        if not meme_winner_role:
            print("Could not find meme winner role for guild: ", guild)
            return

        memechannel = guild.get_channel(db.get_data("SELECT memechannel_id FROM guild_info WHERE guild_id=?", (guild_id,)))
        for member in memechannel.members:
            try:
                await member.remove_roles(meme_winner_role, reason="Meme contest")
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

    @staticmethod
    async def react_to_message(message):
        try:
            await message.add_reaction("\U0001f44d")
        except discord.errors.NotFound:
            print("Message was deleted before we could react!")

    @staticmethod
    async def get_reaction_results(messages, emoji):
        """
            When given a list of :Class: Message and an emoji, will return a list of messages with the most emoji reactions
        """
        max_reactions = 1
        results = []

        for message in messages:
            for reaction in message.reactions:
                if reaction.emoji == emoji and reaction.count > 1 and reaction.count >= max_reactions:  # :thumbsup: or :thumbsdown:
                    results.append(message)
                    if reaction.count > max_reactions:
                        results = [message]
                    max_reactions = reaction.count
        return results, max_reactions - 1

    @staticmethod
    async def get_guild_data(guild_id_tuple):
        data = db.get_data("SELECT * FROM guild_info WHERE guild_id=?", guild_id_tuple)
        return data


def setup(bot):
    bot.add_cog(Memevoting(bot))
