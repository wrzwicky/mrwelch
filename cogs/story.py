import logging, random

import discord, discord.utils
from discord.ext import commands

from story import *

class StoryCog(commands.Cog):
  """tell a joke"""
  def __init__(self, bot):
    self.bot = bot
    self.story = Story()
    
  @commands.command()
  async def joke(self, ctx, *words):
    """tell a joke"""

    joke = "This should be funny to humans:\n" + self.story.tell()
    await ctx.channel.send(joke)

def setup(bot):
  bot.add_cog(StoryCog(bot))
