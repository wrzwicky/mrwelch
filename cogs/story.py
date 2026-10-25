import logging, random

import discord, discord.utils
from discord.ext import commands

from story import *

class StoryCog(commands.Cog):
  """Create algorithmic stories."""
  def __init__(self, bot):
    self.bot = bot
    self.story = Story()
    self.story2 = Story("loveletters.txt")
    
  @commands.command()
  async def joke(self, ctx, *words):
    """Create and tell a funny joke."""
    joke = "This should be funny to humans:\n" + self.story.tell()
    await ctx.reply(joke)

  @commands.command()
  async def love(self, ctx, *words):
    """Write a love letter as from the 1952 "Loveletters" program by Christopher Strachey."""
    letter = self.story2.tell()
    await ctx.reply(letter)

async def setup(bot):
  await bot.add_cog(StoryCog(bot))
