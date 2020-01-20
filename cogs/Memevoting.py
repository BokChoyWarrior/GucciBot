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

    async def meme_contest(self, memechannel_id, prev_scan):

        memechannel = self.bot.get_channel(memechannel_id)

        messages = await memechannel.history(after=prev_scan).flatten()

        if messages:
            winners = await get_winners(messages)
            embedded_winners = await get_winners_embed(winners, self.bot.user.avatar_url)
            await memechannel.send(embed=embedded_winners)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Ready for {self.name}!")

        with open("cogs/cogfigs/Memevoting.json", "r+") as f:
            data = json.load(f)
            self.memechannel_ids = data["memechannel_ids"]
            prev_scan = datetime.fromisoformat(data["last_scan"])
            if self.last_scan - prev_scan > timedelta(7):
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
                try:
                    for message in messages:

                        await message.add_reaction("\U0001f44d")
                        await message.add_reaction("\U0001f44e")
                        await asyncio.sleep(1)
                except discord.HTTPException:
                    pass
                except discord.Forbidden:
                    pass
                except discord.NotFound:
                    pass
                except discord.InvalidArgument:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        prefix = await self.bot.get_prefix(message)
        if message.channel.id in self.memechannel_ids:
            try:
                await message.add_reaction("\U0001f44d")
                await message.add_reaction("\U0001f44e")
            except discord.errors.NotFound:
                print("Message was deleted before we could react!")

    @commands.command()
    async def time(self, ctx):
        await ctx.send(datetime.datetime.now())


async def get_winners(messages):
    """
        When given a list of :Class: Message, will return a list of messages with the most :thumbsup: reactions
    """
    max_win_reactions = 0
    max_lose_reactions = 0
    winners = []
    losers = []
    for message in messages:
        for reaction in message.reactions:
            if reaction.emoji == "\U0001f44d":  # :thumbsup:
                if not winners:
                    winners.append(message)
                    max_win_reactions = reaction.count

                elif reaction.count > max_win_reactions:
                    winners = [message]
                    max_win_reactions = reaction.count

                elif max_win_reactions == reaction.count:
                    winners.append(message)

            elif reaction.emoji == "\U0001f44e":
                if not losers:
                    losers.append(message)
                    max_lose_reactions = reaction.count

                elif reaction.count > max_lose_reactions:
                    losers = [message]
                    max_lose_reactions = reaction.count

                elif max_lose_reactions == reaction.count:
                    losers.append(message)
                pass

    return winners
    #TODO handle losers

async def get_winners_embed(winners, bot_avatar_url):
    embed = discord.Embed(title="**Weekly meme contest!**", colour=discord.Colour(0x4a90e2),
                          description="Below are the most :thumbsup:'d memes of the week",
                          timestamp=datetime.now(tz=timezone.utc))

    embed.set_footer(text="GucciBot", icon_url=bot_avatar_url)

    await get_current_winner_embed(winners, embed)

    return embed


async def get_current_winner_embed(winners, embed):
    for winner in winners:
        if winner.attachments:
            content = winner.attachments[0].url
        else:
            content = winner.content

        author = winner.author.display_name

        if len(winners) == 1:
            embed.set_thumbnail(url=winner.author.avatar_url)
            winner_string = f"**The winner is {author}!**"
            if content.startswith("http"):
                embed.set_image(url=content)
        else:
            winner_string = f"**Joint winner: {author}!**"

        embed.add_field(name=winner_string, value=f"{content}", inline=True)
    return embed


def setup(bot):
    bot.add_cog(Memevoting(bot))
