#!/usr/bin/env python3
import logging, random

import discord, discord.utils
from discord.ext import commands
import inflect
import wordbook

from user_inventory import *

log = logging.getLogger('mrwelch')


class Dictionary(commands.Cog, name="Gratuitous English Word Definer Bot"):
  """Post definitions from dict.org"""

  def __init__(self, bot):
    self.bot = bot


  @commands.command()
  async def define(self, ctx, word: str):
    wb = wordbook.WordBook(host='dict.org', database='wn')
    await wb.connect()
    lines = await wb.define(word)
    desc = "\n".join(lines[2:])

    embedVar = discord.Embed(title=word, description=desc) #, color=0x00ff00)
    #embedVar.set_author(name=lines[0])
    #embedVar.set_thumbnail(url="https://en.wiktionary.org/static/images/project-logos/enwiktionary.png")
    #embedVar.add_field(name="Field1", value="hi", inline=True)
    #embedVar.add_field(name="Field2", value="hi2", inline=True)
    await ctx.channel.send(embed=embedVar)



def setup(bot):
	bot.add_cog(Dictionary(bot))
