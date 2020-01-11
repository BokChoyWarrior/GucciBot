import asyncio
import json
import random
import discord
from discord.ext import commands


async def play_file(filename, message):
    voice_channel = message.author.voice.channel
    ctx = message.channel
    try:
        voice_channel = await voice_channel.connect()
        # catching most common errors that can occur while playing effects
    except discord.Forbidden:
        await ctx.send(
            "Command raised error \"403 Forbidden\". Please check if bot has permission to join and speak in voice "
            "channel")
        return
    except TimeoutError:
        await ctx.send(
            "There was an error while joining channel (Timeout). It's possible that either Discord API or bot host "
            "has latency/connection issues. Please try again later if issues will continue contact bot owner.")
        return
    except discord.ClientException:
        await ctx.send("I am already playing a sound! Please wait to the current sound is done playing!")
        return
    except Exception as e:
        await ctx.send(
            "There was an error processing your request. Please try again. If issues will continue contact bot owner.")
        print(f'Error trying to join a voicechannel: {e}')
        return

    try:
        source = discord.FFmpegPCMAudio(filename)

        # edge case: missing file error
    except FileNotFoundError:
        await ctx.send(
            "There was an issue with playing sound: File Not Found. Its possible that host of bot forgot to copy "
            "over a file. If this error occured on official bot please use D.github to report issue.")

    try:
        voice_channel.play(source, after=lambda: print("played doot"))
        # catching most common errors that can occur while playing effects
    except discord.Forbidden:
        await ctx.send("There was issue playing a sound effect. please check if bot has speak permission")
        await voice_channel.disconnect()
        return
    except TimeoutError:
        await ctx.send(
            "There was a error while attempting to play the sound effect (Timeout) its possible that either discord "
            "API or bot host has latency or network issues. Please try again later, if issues will continue contact "
            "bot owner")
        await voice_channel.disconnect()
        return
    except Exception as e:
        await ctx.send(
            "There was an issue playing the sound. Please try again later. If issues will continue contact bot owner.")
        await voice_channel.disconnect()
        print(f'Error trying to play a sound: {e}')
        return

    # await ctx.send(":thumbsup: played the effect!")
    while voice_channel.is_playing():
        await asyncio.sleep(0.1)

    voice_channel.stop()

    await voice_channel.disconnect()


async def check_for_reply(message):
    try:
        fp = "cogs/cogfigs/Audio.json"
        with open(fp) as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(e, "file path is:", fp, sep=" ")

    for sound_command in data["sound_commands"]:
        word = message_contains(sound_command["phrases"], message)
        if word:
            rick_o_meter = random.randint(1, 100)
            if rick_o_meter != 1:
                fp = "sounds/" + str(random.choice(sound_command["sounds"]))
                fp = bitconnect(fp)
            else:
                fp = "sounds/rickroll.mp3"

            if message.author.voice:
                await play_file(fp, message)
            else:
                f = discord.File(fp, filename=fp)
                await message.author.send(content="", tts=False, embed=None, file=f, files=None, nonce=None)

    for reply_command in data["reply_commands"]:
        word = message_contains(reply_command["phrases"], message)
        if word:
            reply = fetch_reply(word, reply_command)
            await message.channel.send(reply)
            break


def fetch_reply(word, reply_command):
    if reply_command["name"] == "sexism":
        return reply_command["reply_string"].replace("{}", word)


def message_contains(words, message):
    for word in words:
        if word in message.content.lower():
            return word
    return False


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
