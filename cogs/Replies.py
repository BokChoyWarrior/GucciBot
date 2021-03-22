import json
from cogs.utils import utils
from discord.ext import commands


def cache_replies():
    data = {}
    try:
        fp = "cogs/cogfigs/Audio.json"
        with open(fp) as f:
            data = json.load(f)["reply_commands"]
    except FileNotFoundError as error:
        print(error, "file path is:", fp, sep=" ")
    return data


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
