import json
from .utils import utils
from discord.ext import commands


def cache_replies():
    data = {}
    try:
        fp = "cogs/cogfigs/Audio.json"
        with open(fp) as f:
            data = json.load(f)["reply_commands"]
    except FileNotFoundError as e:
        print(e, "file path is:", fp, sep=" ")
    return data
    # for sound_command in data["sound_commands"]:
    #     word = utils.message_contains(sound_command["phrases"], message)
    #     if word:
    #         fp = "sounds/" + str(random.choice(sound_command["sounds"]))
    #         fp = bitconnect(fp)
    #         if message.author.voice:
    #             await utils.play_files(fp, message)
    #             break
    #         # else:
    #         #     f = discord.File(fp, filename=fp)
    #         #     await message.author.send(content="", tts=False, embed=None, file=f, files=None, nonce=None)


def fetch_reply(word, reply_command):
    if reply_command["name"] == "sexism":
        return reply_command["reply_string"].replace("{}", word)


class Replies(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.name = "Replies"
        self.replies_cache = cache_replies()

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        prefix = await self.bot.get_prefix(message)
        if message.author.id == self.bot.user.id:
            return
        if message.content.startswith(prefix):
            pass
        else:
            await self.check_for_reply(message)

    async def check_for_reply(self, message):
        for reply_command in self.replies_cache:
            word = utils.message_contains(reply_command["phrases"], message)
            if word:
                reply = fetch_reply(word, reply_command)
                await message.channel.send(reply)
                break


def setup(bot):
    bot.add_cog(Replies(bot))
