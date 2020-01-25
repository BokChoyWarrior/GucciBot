import asyncio
from datetime import *
import json
import discord
from discord.ext import commands


class Memevoting(commands.Cog):

    def __init__(self, bot):
        self.current_scan = datetime.now()
        self.bot = bot
        self.name = "Memevoting"

    @commands.Cog.listener()
    async def on_ready(self):
        print("memes")

        with open("cogs/cogfigs/Memevoting.json", "r+") as f:
            data = json.load(f)
            self.memechannel_ids = data["memechannel_ids"]
            self.meme_winner_roles = data["meme_winner_roles"]
            self.meme_loser_roles = data["meme_loser_roles"]
            self.prev_scan = datetime.fromisoformat(data["last_scan"])
            print(self.prev_scan, self.current_scan)
            if self.current_scan - self.prev_scan > timedelta(7):
                print("Scanning...")
                for memechannel_id in self.memechannel_ids:
                    await self.meme_contest(memechannel_id, self.prev_scan)
                self.prev_scan += timedelta(7)
                with open("cogs/cogfigs/Memevoting.json", "w+") as f:
                    data["memechannel_ids"] = self.memechannel_ids
                    data["last_scan"] = self.prev_scan.isoformat()
                    json.dump(data, f, indent=2)

            for memechannel_id in self.memechannel_ids:
                memechannel = self.bot.get_channel(memechannel_id)
                messages = await memechannel.history(after=self.prev_scan).flatten()

                for message in messages:
                    if not message.author == self.bot.user:
                        await react_to_messages(message)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        prefix = await self.bot.get_prefix(message)
        if message.channel.id in self.memechannel_ids and message.author != self.bot.user:
            await react_to_messages(message)

    async def meme_contest(self, memechannel_id, prev_scan):

        memechannel = self.bot.get_channel(memechannel_id)
        messages = await memechannel.history(after=prev_scan).flatten()
        if messages:
            winners_messages = await get_results(messages, "\U0001f44d")
            losers_messages = await get_results(messages, "\U0001f44e")

            loser_members = []
            for losers_message in losers_messages:
                embed = await get_loser_embed(losers_message, self.bot.user.avatar_url, losers_messages)
                await memechannel.send(embed=embed)
                member = losers_message.author
                if not member in loser_members:
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
                if not member in winner_members:
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


async def get_results(messages, emoji):
    """
        When given a list of :Class: Message and an emoji, will return a list of messages with the most emoji reactions
    """
    max_reactions = 0
    results = []

    for message in messages:
        for reaction in message.reactions:
            if reaction.emoji == emoji:  # :thumbsup: or :thumbsdown:
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

    embed = discord.Embed(title=head_title, colour=discord.Colour(0x4a90e2), timestamp=datetime.now(tz=timezone.utc))
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

    embed = discord.Embed(title=head_title, colour=discord.Colour(0x4a90e2), timestamp=datetime.now(tz=timezone.utc))
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
