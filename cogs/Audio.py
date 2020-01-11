import random

import discord
import asyncio
import json

from discord.ext import commands

prefix = "!"


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

class Audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = "Audio"

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Ready for {self.name}!")

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    @commands.group()
    async def play(self, ctx):
        pass

    @play.group(name="airhorn")
    async def _Airhorn(self, ctx):
        await play_file("sounds/air horn.mp3", ctx)

    @play.group(name="bloodclart")
    async def _bloodclart(self, ctx):
        await play_file("sounds/Blood clart.mp3", ctx)

    @play.group(name="bloodclot")
    async def _bloodclot(self, ctx):
        await play_file("sounds/Bloodclot.mp3", ctx)

    @play.group(name="blood_clot")
    async def _blood_clot(self, ctx):
        await play_file("sounds/Blood clot.mp3", ctx)

    @play.group(name="cummy")
    async def _cummy(self, ctx):
        await play_file("sounds/Can you guy stop making Cummy say weird shit.mp3", ctx)

    @play.group(name="brainless")
    async def _brainless(self, ctx):
        await play_file("sounds/It's incredible how brainless you are.mp3", ctx)


def setup(bot):
    bot.add_cog(Audio(bot))
