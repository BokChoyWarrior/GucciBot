import asyncio
import discord
import random
from contextlib import contextmanager
from time import perf_counter
from cogs.utils import db


@contextmanager
def measure_time(description: str) -> None:
    t1 = perf_counter()
    yield
    print(f"'{description}' took: {(perf_counter() - t1):.04f} s")


def get_serious_channel_data(guild_id):
    data = db.get_data("SELECT serious_channels FROM guild_info WHERE guild_id=?", (guild_id,))[0]
    data = data.split()
    return data


def channel_is_serious(guild_id, channel_id, data=None):
    if not data:
        data = get_serious_channel_data(guild_id)
    # print(type(channel_id))
    # print(data[guild_id])
    if str(channel_id) in data:
        # print("Found channel")
        return True
    else:
        # print("Didnt find channel")
        return False


def change_seriousness(ctx, channel_id):
    channel_id = str(channel_id)
    guild_id = ctx.guild.id
    data = get_serious_channel_data(guild_id)
    if channel_is_serious(guild_id, channel_id, data=data):
        data.remove(channel_id)
        serious = False
    else:
        data.append(channel_id)
        serious = True
    data = " ".join(data)
    db.set_data("UPDATE guild_info SET serious_channels=? WHERE guild_id=?", (data, guild_id))
    return serious


def check_channel_existence_and_type(channel_id, guild):
    channel_id = int(channel_id)
    for voice_channel in guild.voice_channels:
        if channel_id == voice_channel.id:
            return discord.VoiceChannel
    for text_channel in guild.text_channels:
        if channel_id == text_channel.id:
            return discord.TextChannel
    return False


async def play_files(files, ctx):
    if isinstance(files, str):
        files_to_play = [files]
    else:
        files_to_play = files

    if type(ctx) == discord.ext.commands.Context:
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
        else:
            await ctx.send("You are not connected to a voice channel.", delete_after=10)
    elif type(ctx) == discord.VoiceChannel:
        voice_channel = ctx
    else:
        print("Invalid argument provided (ctx):\n" + repr(ctx))
        return

    if channel_is_serious(voice_channel.guild.id, voice_channel.id):
        return

    voice_join_failures = 0
    if not isinstance(voice_channel, discord.VoiceProtocol):
        voice_join_failures += 1
        if voice_join_failures > 3:
            return
        try:
            voice_channel = await voice_channel.connect()
            # catching most common errors that can occur while playing effects
        except discord.Forbidden:
            await ctx.send(
                "Command raised error \"403 Forbidden\". Please check if bot has permission to join and speak in voice "
                "channel")
            return
        except asyncio.TimeoutError:
            await ctx.send(
                "There was an error while joining channel (Timeout). It's possible that either Discord API or bot host "
                "has latency/connection issues. Please try again later.")
            return
        except discord.ClientException:
            await ctx.send("I am already playing a sound! Please wait until the current sound is done playing!")
            return
        except Exception as e:
            await ctx.send(
                "There was an error processing your request. Please try again. If issues continues, contact bot owner.")
            print(f'Error trying to join a voicechannel: {e}')
            return
    
    rick_o_meter = random.randint(1, 100)
    if rick_o_meter == 1:
        files_to_play = ["sounds/rickroll.mp3"]

    for file in files_to_play:
        try:
            source = discord.FFmpegPCMAudio(file)

            # edge case: missing file error
        except FileNotFoundError:
            await ctx.send(
                "There was an issue with playing sound: File Not Found. Its possible that host of bot forgot to copy "
                "over a file.")

        try:
            voice_channel.play(source)
            # catching most common errors that can occur while playing effects
        except discord.Forbidden:
            await ctx.send("There was an issue playing a sound effect. please check if bot has speak permission")
            await voice_channel.disconnect()
            return
        except TimeoutError:
            await ctx.send(
                "There was an error while attempting to play the sound effect (Timeout) its possible that either discord "
                "API or bot host has latency or network issues. Please try again later, if issues continue, contact "
                "bot owner")
            await voice_channel.disconnect()
            return
        except Exception as e:
            await ctx.send(
                "There was an issue playing the sound. Please try again later. If issues continue, contact bot owner.")
            await voice_channel.disconnect()
            print(f'Error trying to play a sound: {e}')
            return

        while voice_channel.is_playing():
            await asyncio.sleep(0.1)

        voice_channel.stop()

    await voice_channel.disconnect()
    voice_channel.cleanup()


def message_contains(words, message):
    for word in words:
        if word in message.content.lower():
            return word
    return False
