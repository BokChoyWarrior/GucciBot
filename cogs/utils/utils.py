import asyncio
import discord
import random
import json
from contextlib import contextmanager
from time import perf_counter


@contextmanager
def measure_time(description: str) -> None:
    t1 = perf_counter()
    yield
    print(f"'{description}' took: {(perf_counter() - t1):.04f} s")


def get_serious_channel_data():
    try:
        fp = "cogs/cogfigs/SeriousChannels.json"
        with open(fp) as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(e, "file path is:", fp, sep=" ")
    return data


def channel_is_serious(guild_id, channel_id, data=None):
    if not data:
        data = get_serious_channel_data()
        print(type(channel_id))
        print(data[guild_id])
    if channel_id in data[guild_id]:
        print("Found channel")
        return True
    else:
        print("Didnt find channel")
        return False


def change_seriousness(ctx, channel_id):
    channel_id = str(channel_id)
    guild_id = str(ctx.guild.id)
    data = get_serious_channel_data()

    with open("cogs/cogfigs/SeriousChannels.json", "w+") as f:
        if channel_is_serious(guild_id, channel_id, data):
            data[guild_id].remove(channel_id)
            serious = False
        else:
            data[guild_id].append(channel_id)
            serious = True
        json.dump(data, f, indent=2)
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


async def play_files(files, ctx, message=None, channel=None):
    if isinstance(files, str):
        files_to_play = [files]
    else:
        files_to_play = files

    if channel:
        voice_channel = channel
    else:
        voice_channel = message.author.voice.channel
        ctx = message.channel

    if channel_is_serious(voice_channel.id):
        return

    voice_join_failures = 0

    for file in files_to_play:
        if not isinstance(voice_channel, discord.VoiceProtocol):
            voice_join_failures += 1
            if voice_join_failures > 3:
                return
            print("Not connected to a voice protocol")
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
            filename = "sounds/rickroll.mp3"

        try:
            source = discord.FFmpegPCMAudio(file)

            # edge case: missing file error
        except FileNotFoundError:
            await ctx.send(
                "There was an issue with playing sound: File Not Found. Its possible that host of bot forgot to copy "
                "over a file.")

        try:
            voice_channel.play(source, after=lambda: print("played doot"))
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


def message_contains(words, message):
    for word in words:
        if word in message.content.lower():
            return word
    return False
