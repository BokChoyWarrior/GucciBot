import asyncio
import datetime as dt
import json
import discord
from discord.ext import commands


class Memevoting(commands.Cog):

    def __init__(self, bot):
        self.current_scan = dt.datetime.now()
        self.bot = bot
        self.name = "Memevoting"
        self.bg_task = self.bot.loop.create_task(self.meme_contest_bg_task())

    @commands.Cog.listener()
    async def on_ready(self):

        with open("cogs/cogfigs/Memevoting.json", "r+") as f:
            self.data = json.load(f)
            self.memechannel_ids = self.data["memechannel_ids"]
            self.meme_winner_roles = self.data["meme_winner_roles"]
            self.meme_loser_roles = self.data["meme_loser_roles"]
            self.prev_scan = dt.datetime.fromisoformat(self.data["last_scan"])

            for memechannel_id in self.memechannel_ids:
                memechannel = self.bot.get_channel(memechannel_id)
                messages = await memechannel.history(after=self.prev_scan).flatten()

                for message in messages:
                    if not message.author == self.bot.user:
                        await react_to_messages(message)

    async def meme_contest_bg_task(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # so that the prev_scan value can be fetched before running the following code
        while not self.bot.is_closed():
            self.current_scan = dt.datetime.now()
            if dt.timedelta(2) < self.current_scan - self.prev_scan < dt.timedelta(7):
                for memechannel_id in self.memechannel_ids:
                    for member in self.bot.get_channel(memechannel_id).members:
                        for meme_loser_role in self.meme_loser_roles:
                            try:
                                await member.remove_roles(member.guild.get_role(meme_loser_role))
                            except AttributeError:
                                pass
                        for meme_winner_role in self.meme_winner_roles:
                            try:
                                await member.remove_roles(member.guild.get_role(meme_winner_role))
                            except AttributeError:
                                pass

            if self.current_scan - self.prev_scan > dt.timedelta(7):
                print("Scanning...", self.current_scan - self.prev_scan)
                for memechannel_id in self.memechannel_ids:
                    await self.get_meme_contest_results(memechannel_id, self.prev_scan)
                self.prev_scan += dt.timedelta(7)
                with open("cogs/cogfigs/Memevoting.json", "w+") as f:
                    self.data["memechannel_ids"] = self.memechannel_ids
                    self.data["last_scan"] = self.prev_scan.isoformat()
                    json.dump(self.data, f, indent=2)

            await asyncio.sleep(1800)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel.id in self.memechannel_ids and message.author != self.bot.user:
            await react_to_messages(message)

    async def get_meme_contest_results(self, memechannel_id, prev_scan):

        memechannel = self.bot.get_channel(memechannel_id)
        messages = await memechannel.history(after=prev_scan).flatten()
        if messages:
            winners_messages = await get_reaction_results(messages, "\U0001f44d")
            losers_messages = await get_reaction_results(messages, "\U0001f44e")

            loser_members = []
            for losers_message in losers_messages:
                embed = await get_loser_embed(losers_message, self.bot.user.avatar_url, losers_messages)
                await memechannel.send(embed=embed)
                member = losers_message.author
                if member not in loser_members:
                    for meme_loser_role in self.meme_loser_roles:
                        try:
                            await member.add_roles(member.guild.get_role(meme_loser_role))
                        except AttributeError:
                            pass
                    loser_members.append(member)

            winner_members = []
            for winners_message in winners_messages:
                embed = await get_winner_embed(winners_message, self.bot.user.avatar_url, winners_messages)
                await memechannel.send(embed=embed)

                member = winners_message.author
                if not (member in winner_members or member in loser_members):
                    for meme_winner_role in self.meme_winner_roles:
                        try:
                            await member.add_roles(member.guild.get_role(meme_winner_role))
                        except AttributeError:
                            pass

                    winner_members.append(member)


async def react_to_messages(message):
    try:
        await message.add_reaction("\U0001f44d")
        await asyncio.sleep(0.3)
        await message.add_reaction("\U0001f44e")
        await asyncio.sleep(0.3)
    except discord.errors.NotFound:
        print("Message was deleted before we could react!")


async def get_reaction_results(messages, emoji):
    """
        When given a list of :Class: Message and an emoji, will return a list of messages with the most emoji reactions
    """
    max_reactions = 0
    results = []

    for message in messages:
        for reaction in message.reactions:
            if reaction.emoji == emoji and reaction.count > 1:  # :thumbsup: or :thumbsdown:
                if not results:
                    results.append(message)
                    max_reactions = reaction.count
                elif reaction.count > max_reactions:
                    results = [message]
                    max_reactions = reaction.count
                elif max_reactions == reaction.count:
                    results.append(message)
    return results


async def get_winner_embed(winner, bot_avatar_url, winners):
    if len(winners) > 1:
        head_title = "\U0001f923 Weekly best memes! \U0001f923"
    else:
        head_title = "\U0001f923 This week's UlTiMaTe meme! \U0001f923"

    embed = discord.Embed(title=head_title, colour=discord.Colour(0x4a90e2),
                          timestamp=dt.datetime.now(tz=dt.timezone.utc))
    embed.set_thumbnail(url=winner.author.avatar_url)
    embed.set_footer(text="GucciBot", icon_url=bot_avatar_url)

    if winner.attachments:
        content = winner.attachments[0].url
    else:
        content = winner.content
    if content.startswith("http"):
        embed.set_image(url=content)
        content_value = f"[Link]({content})"
    else:
        content_value = content
        pass
    embed.add_field(name=f"**Sent by memelord {winner.author.display_name}!**", value=content_value)

    return embed


async def get_loser_embed(loser, bot_avatar_url, losers):
    if len(losers) > 1:
        head_title = "\U0001F4A9 Weekly worst memes! \U0001F4A9"
    else:
        head_title = "\U0001F4A9 This week's ShItTeSt meme! \U0001F4A9"

    embed = discord.Embed(title=head_title, colour=discord.Colour(0x4a90e2),
                          timestamp=dt.datetime.now(tz=dt.timezone.utc))
    embed.set_thumbnail(url=loser.author.avatar_url)
    embed.set_footer(text="GucciBot", icon_url=bot_avatar_url)

    if loser.attachments:
        content = loser.attachments[0].url
    else:
        content = loser.content
    if content.startswith("http"):
        embed.set_image(url=content)
        content_value = f"[Link]({content})"
    else:
        content_value = content
        pass
    embed.add_field(name=f"**Sent by boring loser {loser.author.display_name}!**", value=content_value)

    return embed


def setup(bot):
    bot.add_cog(Memevoting(bot))
