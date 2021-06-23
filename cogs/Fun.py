import asyncio

import discord
from discord.ext import commands


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Fun"

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # kav
    # 114786142619959303
    # gucci
    # 114458356491485185
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == 114458356491485185 and (after.deaf or after.mute):
            kav = member.guild.get_member(114786142619959303)
            try:
                while (member.voice.mute or member.voice.deaf):
                    if after.deaf:
                        await member.edit(deafen=False)
                        await kav.edit(deafen=True)
                    if after.mute:
                        await member.edit(mute=False)
                        await kav.edit(mute=True)
                    asyncio.sleep(1)

            except Exception:
                pass


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if not message.guild:
            return
        if message.guild.get_role(668798124751323146) in message.author.roles:
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
                new_message += letter_to_add
            await message.channel.send(content=new_message, file=discord.File("pictures/spongebob-mocking.jpg"),
                                       delete_after=60)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def message(self, ctx, *args):
        my_message = " ".join(args)
        await ctx.message.delete()
        await ctx.send(my_message)

    @commands.command()
    async def bunker(self, ctx):
        await ctx.send("https://tech4thewin.com/wp-content/uploads/2020/08/9037547777323607125.jpg")

    @commands.command()
    async def satellite(self, ctx):
        await ctx.send(file=discord.File('pictures/warzone-satellites.png'))

    async def rename_all_members(self, guild_id, name):
        for member in self.bot.get_guild(guild_id).members:
            await asyncio.sleep(1)
            try:
                await member.edit(reason="Meme contest winner request", nick=name)
            except discord.Forbidden:
                print("Forbidden rename on: " + str(member.__repr__))
            except discord.HTTPException:
                print("HTTP exception")


def setup(bot):
    bot.add_cog(Fun(bot))
