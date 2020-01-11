import asyncio
import json
import random
import discord
from .utils import utils
from discord.ext import commands


async def check_for_reply(message):
    try:
        fp = "cogs/cogfigs/Audio.json"
        with open(fp) as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(e, "file path is:", fp, sep=" ")

    for sound_command in data["sound_commands"]:
        word = utils.message_contains(sound_command["phrases"], message)
        if word:
            rick_o_meter = random.randint(1, 100)
            if rick_o_meter != 1:
                fp = "sounds/" + str(random.choice(sound_command["sounds"]))
                fp = bitconnect(fp)
            else:
                fp = "sounds/rickroll.mp3"

            if message.author.voice:
                await utils.play_file(fp, message)
            else:
                f = discord.File(fp, filename=fp)
                await message.author.send(content="", tts=False, embed=None, file=f, files=None, nonce=None)

    for reply_command in data["reply_commands"]:
        word = utils.message_contains(reply_command["phrases"], message)
        if word:
            reply = fetch_reply(word, reply_command)
            await message.channel.send(reply)
            break


def fetch_reply(word, reply_command):
    if reply_command["name"] == "sexism":
        return reply_command["reply_string"].replace("{}", word)


def bitconnect(fp):
    if fp == "sounds/btc":
        num = random.randint(1, 43)
        fp = f"sounds/bitconnect/Bitconnect{num}.mp3"

    return fp


class Replies(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Replies"

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Ready for {self.name}!")

    @commands.Cog.listener()
    async def on_message(self, message):
        prefix = await self.bot.get_prefix(message)
        if message.author.id == self.bot.user.id:
            return
        if message.content.startswith(prefix):
            pass
        else:
            await check_for_reply(message)




def setup(bot):
    bot.add_cog(Replies(bot))
