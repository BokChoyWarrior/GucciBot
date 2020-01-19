import discord
from discord.ext import commands


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Fun"

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Ready for {self.name}!")

    @commands.Cog.listener()
    async def on_message(self, message):
        prefix = await self.bot.get_prefix(message)
        if message.author.id == 97054487398592512 or message.author.id == 189449798280019968\
                or message.author.id == 281128026048036864 or message.author.id == 95945852501127168:
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
        # TODO: do not send message if no content (and only for role)

def setup(bot):
    bot.add_cog(Fun(bot))
