import discord
from discord.ext import commands


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Fun"

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        prefix = await self.bot.get_prefix(message)
        if message.guild.get_role(668798124751323146) in message.guild.get_member(message.author.id).roles:
            if message.content.startswith("http") or message.content == "":
                return
            new_message = ""
            i = 0
            for letter in message.content.casefold():
                if i == 0:
                    letter_to_add = letter.swapcase()
                    i += 1
                else:
                    letter_to_add = letter
                    i -= 1
                new_message = new_message + letter_to_add
            await message.channel.send(content=new_message, file=discord.File("pictures/spongebob-mocking.jpg"),
                                       delete_after=60)
        pass


def setup(bot):
    bot.add_cog(Fun(bot))
