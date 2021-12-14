import logging, random

import discord, discord.utils
from discord.ext import commands

class DiceCog(commands.Cog, name="Totally random dice roller"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, word: str = None):
      if not word:
        await ctx.message.add_reaction("\N{SHRUG}")
      else:        
        await ctx.channel.send("9")

def setup(bot):
	bot.add_cog(DiceCog(bot))
