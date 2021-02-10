import random

from .utils import utils
from discord.ext import commands

import pyttsx3

prefix = "!"


class Audio(commands.Cog, name="Audio"):
    def __init__(self, bot):
        self.bot = bot
        self.name = "Audio"
        self.playing = False

    @commands.command()
    async def stop(self, ctx):
        """Stops any voice activity and disconnects the bot from the voice channel."""
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    """ AOE2 sounds """

    @commands.group()
    async def aoe2(self, ctx):
        """Play a sound from AoE:II."""
        pass

    @aoe2.group(name="11")
    async def _11(self, ctx):
        await utils.play_files("sounds/aoe2/11.ogg", ctx)

    @aoe2.group(name="12")
    async def _12(self, ctx):
        await utils.play_files("sounds/aoe2/12.ogg", ctx)

    @aoe2.group(name="13")
    async def _13(self, ctx):
        await utils.play_files("sounds/aoe2/13.ogg", ctx)

    @aoe2.group(name="14")
    async def _14(self, ctx):
        await utils.play_files("sounds/aoe2/14.ogg", ctx)

    @aoe2.group(name="30")
    async def _30(self, ctx):
        await utils.play_files("sounds/aoe2/30.ogg", ctx)

    """ 
    PLAY commands 
    Very fun!
    
    """

    @commands.group()
    async def play(self, ctx):
        """Plays the given sound."""
        pass

    @play.group(name="airhorn", aliases=["horn"])
    async def _Airhorn(self, ctx):
        await utils.play_files("sounds/air horn.mp3", ctx)

    @play.group(name="weed", aliases=["420"])
    async def _Weed(self, ctx):
        await utils.play_files("sounds/Weed.mp3", ctx)

    @play.group(name="bloodclart")
    async def _bloodclart(self, ctx):
        await utils.play_files("sounds/Blood clart.mp3", ctx)

    @play.group(name="bloodclot")
    async def _bloodclot(self, ctx):
        await utils.play_files("sounds/Bloodclot.mp3", ctx)

    @play.group(name="blood_clot")
    async def _blood_clot(self, ctx):
        await utils.play_files("sounds/Blood clot.mp3", ctx)

    @play.group(name="btc", aliases=["bitcoin"])
    async def _btc(self, ctx):
        btc = random.randint(0, 41)
        sound_path = f"sounds/bitconnect/Bitconnect{btc}.mp3"
        await utils.play_files(sound_path, ctx)

    @play.group(name="hamburger", aliases=["burger"])
    async def _hamburger(self, ctx):
        await utils.play_files("sounds/Hamburger.mp3", ctx)

    @play.group(name="dipesh", aliases=["dippstar"])
    async def _dipesh(self, ctx):
        await utils.play_files("sounds/xplozionz.mp3", ctx)

    @play.group(name="excluded")
    async def _excluded(self, ctx):
        await utils.play_files("sounds/excluded.mp3", ctx)

    @play.group(name="cappuccino")
    async def _cappuccino(self, ctx):
        await utils.play_files("sounds/cappuccino.mp3", ctx)

    @play.group(name="kav")
    async def _kav(self, ctx):
        await utils.play_files("sounds/Kav=.mp3", ctx)

    @play.group(name="spongebob")
    async def _spongebob(self, ctx):
        await utils.play_files("sounds/spongebob.mp3", ctx)

    @play.group(name="xavier", aliases=["xra"])
    async def _xavier(self, ctx):
        await utils.play_files("sounds/xra sb.mp3", ctx)

    @play.group(name="gnaron")
    async def _gnaron(self, ctx):
        await utils.play_files("sounds/Koksockar.mp3", ctx)

    """ SAY COMMAND """
    @commands.command(help="Speaks your message with pyttsx3 text-to-speech.",
                      usage="""\"text\"
    
    Where your *text* is enclosed in quotes.""")
    async def say(self, ctx, text, lang="en"):
        """Speaks your message with pyttsx3 text-to-speech."""
        try:
            if ctx.message.author.voice is not None and not self.playing:
                try:
                    self.playing = True
                    with utils.measure_time("Creating pyttsx3 mp3"):
                        tts_engine = pyttsx3.init()
                        tts_engine.save_to_file(text, "sounds/say.mp3")
                        print("Saved to file")
                        tts_engine.runAndWait()
                        print("Ran and waited")

                    await utils.play_files("sounds/say.mp3", ctx)
                except Exception as e:
                    await ctx.send(content=f"There was an error processing your request.\n\nTechnical details:\n`{e}`", delete_after=60)
                    return
            else:
                if self.playing:
                    await ctx.send(content="Please wait until the current sound is finished playing, or type `!stop` to end it.", delete_after=60)
                elif ctx.message.author.voice:
                    await ctx.send(content="Cannot play sound.", delete_after=60)
        except Exception as e:
            print(e)
        finally:
            self.playing = False

def setup(bot):
    bot.add_cog(Audio(bot))
