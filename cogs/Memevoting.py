import asyncio
from datetime import *
import json
import discord
from discord.ext import commands


class Memevoting(commands.Cog):

    def __init__(self, bot):
        self.last_scan = datetime.now()
        self.bot = bot
        self.name = "Memevoting"

    @commands.Cog.listener()
    async def on_ready(self):

        with open("cogs/cogfigs/Memevoting.json", "r+") as f:
            data = json.load(f)
            self.memechannel_ids = data["memechannel_ids"]
            prev_scan = datetime.fromisoformat(data["last_scan"])
            if self.last_scan - prev_scan > timedelta(7):
                self.last_scan += timedelta(7)
                print("Scanning...")
                for memechannel_id in self.memechannel_ids:
                    await self.meme_contest(memechannel_id, prev_scan)
                with open("cogs/cogfigs/Memevoting.json", "w+") as f:
                    data["memechannel_ids"] = self.memechannel_ids
                    data["last_scan"] = self.last_scan.isoformat()
                    json.dump(data, f, indent=2)

            for memechannel_id in self.memechannel_ids:
                memechannel = self.bot.get_channel(memechannel_id)
                messages = await memechannel.history(after=prev_scan).flatten()

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

    @commands.command()
    async def time(self, ctx):
        await ctx.send(datetime.datetime.now())

    async def meme_contest(self, memechannel_id, prev_scan):

        memechannel = self.bot.get_channel(memechannel_id)

        messages = await memechannel.history(after=prev_scan).flatten()

        if messages:
            winners = await get_results(messages, "\U0001f44d")
            losers = await get_results(messages, "\U0001f44e")

            for winner in winners:
                embed = await get_winner_embed(winner, self.bot.user.avatar_url, winners)
                await memechannel.send(embed=embed)


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


def setup(bot):
    bot.add_cog(Memevoting(bot))
