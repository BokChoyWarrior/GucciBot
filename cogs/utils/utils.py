import asyncio
import discord
import random
import json


def channel_is_serious(givenchannelid, data=None):
    if not data:
        try:
            fp = "cogs/cogfigs/SeriousChannels.json"
            with open(fp) as f:
                data = json.load(f)
        except FileNotFoundError as e:
            print(e, "file path is:", fp, sep=" ")
    for channelId in data["channelIds"]:
        if givenchannelid == channelId:
            return True
    return False


def change_seriousness(givenchannelid):
    data = {}
    try:
        fp = "cogs/cogfigs/SeriousChannels.json"
        with open(fp) as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(e, "file path is:", fp, sep=" ")
    with open("cogs/cogfigs/SeriousChannels.json", "w+") as f:
        if channel_is_serious(givenchannelid, data):
            data["channelIds"].remove(givenchannelid)
        else:
            data["channelIds"].append(givenchannelid)
        json.dump(data, f, indent=2)


def channel_exists(givenchannelid, guild):
    for voice_channel in guild.voice_channels:
        if givenchannelid == voice_channel.id:
            return True
    return False


async def play_file(filename, message=None, channel=None):
    rick_o_meter = random.randint(1, 100)
    if rick_o_meter == 1:
        filename = "sounds/rickroll.mp3"

    if channel:
        voice_channel = channel
    else:
        voice_channel = message.author.voice.channel
        ctx = message.channel

    if channel_is_serious(voice_channel.id):
        return

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

    try:
        source = discord.FFmpegPCMAudio(filename)

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
