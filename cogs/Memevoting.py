import asyncio
import datetime as dt
import json
import discord
from discord.ext import commands


class Memevoting(commands.Cog):

    def __init__(self, bot):
        # Below is a sample of the current storage format of the meme channels and such for each guild.
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

        self.bot = bot
        self.name = "Memevoting"
        with open("cogs/cogfigs/Memevoting.json", "r+") as f:
            self.data = json.load(f)
        self.guild_ids = self.data["guild_ids"]
        self.prev_scan = dt.datetime.fromisoformat(self.data["last_scan"])
        self.current_scan = dt.datetime.utcnow()
        self.bg_task = self.bot.loop.create_task(self.meme_contest_bg_task())

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id in self.guild_ids:
            memechannel = self.bot.get_channel(self.guild_ids[guild_id]["memechannel_id"])
            messages = await memechannel.history(after=self.prev_scan).flatten()
            for message in messages:
                if not message.author == self.bot.user:
                    await self.react_to_message(message)

    async def meme_contest_bg_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.current_scan = dt.datetime.utcnow()
            if dt.timedelta(2) < self.current_scan - self.prev_scan < dt.timedelta(7):
                await self.remove_meme_roles()  # make this function find guild

            if self.current_scan - self.prev_scan > dt.timedelta(7):
                print("Scanning...", self.current_scan - self.prev_scan)
                await self.get_meme_contest_results()
                self.prev_scan += dt.timedelta(7)
                with open("cogs/cogfigs/Memevoting.json", "w+") as f:
                    self.data["last_scan"] = self.prev_scan.isoformat()
                    json.dump(self.data, f, indent=2)

            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if str(message.channel.id) == str(
                self.guild_ids[str(message.guild.id)]["memechannel_id"]) and message.author != self.bot.user:
            await self.react_to_message(message)

    async def get_result_embed(self, participant_msg, winner_or_loser, emoji=""):
        if winner_or_loser == "winner":
            head_title = "\U0001f923 This week's UlTiMaTe memes! \U0001f923"
            congrats_message = "Sent by memelord: "
        elif winner_or_loser == "loser":
            head_title = "\U0001F4A9 This week's ShItTeSt memes! \U0001F4A9"
            congrats_message = "Sent by boring loser: "

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

    async def get_meme_contest_results(self):
        for guild_id in self.guild_ids:
            guild = self.bot.get_guild(int(guild_id))
            meme_loser_role = guild.get_role(int(self.guild_ids[guild_id]["meme_loser_role_id"]))
            meme_winner_role = guild.get_role(int(self.guild_ids[guild_id]["meme_winner_role_id"]))
            memechannel = guild.get_channel(int(self.guild_ids[guild_id]["memechannel_id"]))
            memeresultchannel = guild.get_channel(int(self.guild_ids[guild_id]["memeresultchannel_id"]))
            messages = await memechannel.history(after=self.prev_scan).flatten()
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
                    await member.add_roles(meme_winner_role, reason="meme contest")
                except discord.Forbidden as e:
                    print(e + " - You do not have permission to add these roles.")
                except discord.HTTPException as e:
                    print(e)

    async def remove_meme_roles(self):
        for guild_id in self.guild_ids:
            guild = self.bot.get_guild(int(guild_id))

            valid_roles = []
            meme_loser_role = guild.get_role(int(self.guild_ids[guild_id]["meme_loser_role_id"]))
            if meme_loser_role:
                valid_roles.append(meme_loser_role)
            meme_winner_role = guild.get_role(int(self.guild_ids[guild_id]["meme_winner_role_id"]))
            if meme_winner_role:
                valid_roles.append(meme_winner_role)
            memechannel = guild.get_channel(int(self.guild_ids[guild_id]["memechannel_id"]))

            if not len(valid_roles) > 0:
                continue

            for member in memechannel.members:
                try:
                    await member.remove_roles(*valid_roles, reason="Meme contest")
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


def setup(bot):
    bot.add_cog(Memevoting(bot))
