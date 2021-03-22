import discord

ZERO_WIDTH_CHAR = "\u200b"
EMBED_COLOUR = discord.Colour.from_rgb(0, 255, 255)
def GET_BASE_EMBED():
    return discord.Embed(colour=EMBED_COLOUR)
