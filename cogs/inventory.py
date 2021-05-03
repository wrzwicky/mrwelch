#!/usr/bin/env python3
import logging, random

import discord, discord.utils
from discord.ext import commands
import inflect

from user_inventory import *

log = logging.getLogger('mrwelch')



class InventoryCog(commands.Cog, name="Inventory Commands"):
  allInventory = {} #{member -> []}


  def __init__(self, bot):
    self.bot = bot

    # https://pypi.org/project/inflect/
    self.inflector = inflect.engine()


  # @commands.Cog.listener()
  # async def on_member_join(self, member):
  #   channel = member.guild.system_channel
  #   if channel is not None:
  #     await channel.send('Welcome {0.mention}.'.format(member))

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
    """Gives item"""
    log.info(f"Giving {item} to {user}")
    if user and item:
      inv = self._inv(user)
      if not inv.has(item):
        inv.add(item)
        if user == self.bot.user:
          await ctx.channel.send("Thank you!")
        else:
          await ctx.channel.send(f"{ctx.author.name} gave {item} to {user}.")
      else:
        if user == self.bot.user:
          await ctx.channel.send("No thank you.")
        else:
          await ctx.channel.send(f"Too many of those floating around.")

  @commands.command()
  async def take(self, ctx, item: str):
    """find all people with item, pick one at random, take it from them"""
    if item:
      victims = [u for u in self.allInventory if self.allInventory[u].see(item)]
      if victims:
        v = random.choice(victims)
        self._inv(v).remove(item)
        self._inv(v).add(item)
        resp = f"You \"found\" {v.name}'s {item}!"
      else:
        resp = f"You don't see any {item}."
      await ctx.channel.send(resp)

# if itme=="one ring" put directly into pocket, ^i says 'pocketses'
# if item=='nothing' say 'thanks for nothing'
# bot puts everything in pockets
# gave user (a|some) item(s)
# what if extra args?
# what if item is user or guild etc?
# if user give gun to mrwelch, "mrwelch uses gun to take everything from user"

#if member = bot, say "Thank you!"
# No thanks, mrwelch is independently wealchy.

  @commands.command()
  async def drop(self, ctx, item: str):
    user = ctx.author
    if user in self.allInventory:
      inv = self.allInventory[user]
      if inv.has(item):
        inv.remove(item)
        await ctx.channel.send("Dropped.")

  @commands.command(aliases=['i'])
  async def inventory(self, ctx, user: discord.Member = None):
    if not user:
      user = ctx.author
      intro = "You have"
    elif user == self.bot.user:
      intro = "I have"
    else:
      intro = user.name + " has"

    desc = None
    if user in self.allInventory:
      desc = self.allInventory[user].describe()
    if not desc:
      desc = "nothing"
    await ctx.channel.send(f"{intro} {desc}.")

  @commands.command()
  async def pocket(self, ctx, item: str):
    if item and ctx.author in self.allInventory:
      inv = self.allInventory[ctx.author]
      if not inv:
        resp = "You have nothing."
      elif not inv.has(item):
        resp = "You don't have that."
      else:
        inv.pocket(item)
        resp = "Pocketed."
      await ctx.channel.send(resp)

  @commands.command()
  async def reboot(self, ctx):
    await ctx.channel.send("Who do you think you are?!")




#take?
#inventory
#pocket
#use

# give user item
# inventory (name)
#   -> (items) and something in his pockets
# drop item
# pocket item


def setup(bot):
	bot.add_cog(InventoryCog(bot))
