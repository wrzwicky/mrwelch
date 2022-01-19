#!/usr/bin/env python3
import logging, random

import discord, discord.utils
from discord.ext import commands
import inflect

from user_inventory import *

log = logging.getLogger('mrwelch')


def single(p,noun):
  """Patch inflect -- singular_noun returns False if noun is already singular. This makes it return noun"""
  s = p.singular_noun(noun)
  if s:
    return s
  else:
    return noun


class InventoryCog(commands.Cog):
  """Weird little per-user inventory keeper"""
  
  allInventory = {} #{member -> []}


  def __init__(self, bot):
    self.bot = bot

    # https://pypi.org/project/inflect/
    self.inflector = inflect.engine()


  def _add(self, user, item):
    if not user in self.allInventory:
      self.allInventory[user] = UserInventory()
    self.allInventory[user].add(item)

  def _remove(self, user, item):
    if user in self.allInventory:
      self.allInventory[user].remove(item)

  def _inv(self, user):
    if user in self.allInventory:
      return self.allInventory[user]
    else:
      inv = UserInventory()
      self.allInventory[user] = inv
      return inv


  @commands.command()
  async def give(self, ctx, user: discord.Member, item: str):
    """give <item> to <user>"""
    if user and item:
      item = single(self.inflector, item)
      log.info(f"Giving {item} to {user}")
      inv = self._inv(user)
      if not inv.has(item):
        inv.add(item)
        if user == self.bot.user:
          # bot puts everything in pockets
          inv.pocket(item)
          # if item=='nothing' say 'thanks for nothing'
          if item.lower() == "nothing":
            await ctx.channel.send("Thanks for nothing.")
          else:
            await ctx.channel.send("Thank you!")
        else:
          #await ctx.channel.send(f"{ctx.author.mention} gave {self.inflector.a(item)} to {user.mention}.")
          await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
      else:
        if user == self.bot.user:
          #await ctx.channel.send("No thank you.")
          await ctx.channel.send("No thanks, mrwelch is independently wealchy.")
        else:
          await ctx.channel.send(f"Too many of those floating around.")

  @commands.command()
  async def take(self, ctx, item: str):
    """find all people with <item>, pick one at random, take it from them"""
    if item:
      item = single(self.inflector, item)
      victims = [u for u in self.allInventory if self.allInventory[u].see(item)]
      if victims:
        v = random.choice(victims)
        self._inv(v).remove(item)
        self._inv(ctx.author).add(item)
        resp = f"You \"found\" {v.name}'s {item}!"
      else:
        resp = f"You don't see any {item}."
      await ctx.channel.send(resp)

  @commands.command()
  async def drop(self, ctx, item: str):
    """delete the <item> if you have it"""
    if item:
      item = single(self.inflector, item)
      user = ctx.author
      if user in self.allInventory:
        inv = self.allInventory[user]
        if inv.has(item):
          inv.remove(item)
          await ctx.channel.send("Dropped.")

  @commands.command()
  async def use(self, ctx, item: str):
    """use (and delete) the <item>"""
    if item:
      item = single(self.inflector, item)
      user = ctx.author
      if user in self.allInventory:
        inv = self.allInventory[user]
        if inv.has(item):
          inv.remove(item)
          await ctx.channel.send(f"You drank the {item}.")

  @commands.command(aliases=['i'])
  async def inventory(self, ctx, user: discord.Member = None):
    """list all items you or <user> posess(es)"""
    if not user:
      user = ctx.author
      intro = "You have"
    elif user == self.bot.user:
      intro = "I have"
    else:
      intro = user.mention + " has"

    desc = None
    if user in self.allInventory:
      desc = self.allInventory[user].describe()
    if not desc:
      desc = "nothing"
    await ctx.channel.send(f"{intro} {desc}.")

  @commands.command()
  async def pocket(self, ctx, item: str):
    """hide <item> from other users"""
    resp = None
    if item:
      inv = self.allInventory.get(ctx.author)
      if not inv or inv.isEmpty():
        #resp = "You have nothing."
        await ctx.message.add_reaction("\N{SHRUG}") #("\N{NO ENTRY}")
      elif not inv.has(item):
        #resp = "You don't have that."
        await ctx.message.add_reaction("\N{SHRUG}")
      else:
        inv.pocket(item)
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
      if resp: await ctx.channel.send(resp)

  @commands.command(hidden=True)
  async def reboot(self, ctx):
    await ctx.channel.send("Who do you think you are?!")



def setup(bot):
	bot.add_cog(InventoryCog(bot))



# give user item
#take
# drop item
#use
# inventory (name)
#   -> (items) and something in his pockets
# pocket item


#TODO
# if 'item' is plural, command should affect all
# allow private ^i
# use collections.Counter in user_inventory
# what if extra args?
# what if item is user or guild etc?
# if user give gun to mrwelch, "mrwelch uses gun to take everything from user"
# private DM with full inventory
# use reactions instead of text
#   await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
#   emoji = '\N{THUMBS UP SIGN}'   #https://www.fileformat.info/info/emoji/list.htm
#   bot.get_emoji
# if item='nothing', don't give, maybe reaction=confusion

#TODONE
# add inflect to user_inventory
# if itme=="one ring" put directly into pocket, ^i says 'pocketses'
# gave user (a|some) item(s)
# all user names should be proper @refs
# - user.mention
# if member = bot, say "Thank you!"
