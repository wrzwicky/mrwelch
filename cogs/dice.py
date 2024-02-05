import logging, random

import discord, discord.utils
from discord.ext import commands

class DiceCog(commands.Cog):
    """Roll things."""

    def __init__(self, bot):
        self.bot = bot

        self.up = "abcdefghijklmnopqrstuvwxyz" + \
                  "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + \
                  "1234567890" + \
                  "!@#$%^&*()-=_+" + \
                  "[]\;',./{}|:\"<>?" + \
                  ""
        self.down = "ɐqɔpǝɟƃɥıɾʞןɯuodbɹsʇnʌʍxʎz" + \
                    "∀qϽᗡƎℲפHIſʞ˥WNOԀὉᴚS⊥∩ΛMX⅄Z" + \
                    "ƖᄅƐㄣϛ9ㄥ860" + \
                    "¡@#$%^⅋*)(-=‾+" + \
                    "][\\;,'˙/}{|:,><¿" + \
                    ""

    @commands.command()
    async def roll(self, ctx, *words):
      """roll things over"""
      if not words:
        await ctx.message.add_reaction("\N{SHRUG}")
      else:
        word = " ".join(words)
        #s = "9"
        s = "".join([self.derp(c) for c in word[::-1]])
        await ctx.channel.send(s)

    def derp(self, c):
      try:
        return self.down[self.up.index(c)]
      except:
        return c

def setup(bot):
	bot.add_cog(DiceCog(bot))
