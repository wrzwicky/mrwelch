#!/usr/bin/env python3
import json
import logging, random
import os
from pathlib import Path

import discord, discord.utils
from discord.ext import commands
import inflect

from user_inventory import *

log = logging.getLogger('mrwelch')

DATA_VERSION = 1
DEFAULT_STORAGE_PATH = Path(__file__).resolve().parent.parent / "data" / "inventories.json"


class InventoryPersistenceError(RuntimeError):
  """Raised when saved inventory data cannot safely be loaded or written."""


def single(p,noun):
  """Patch inflect -- singular_noun returns False if noun is already singular. This makes it return noun"""
  s = p.singular_noun(noun)
  if s:
    return s
  else:
    return noun


class InventoryCog(commands.Cog):
  """Weird little per-user inventory keeper"""

  def __init__(self, bot, storage_path=None):
    self.bot = bot
    self.storage_path = Path(storage_path or DEFAULT_STORAGE_PATH)
    self.allInventory = self._load_inventory()
    # https://pypi.org/project/inflect/
    self.inflector = inflect.engine()

  @staticmethod
  def _user_id(user):
    return user if isinstance(user, int) else user.id

  def _load_inventory(self):
    if not self.storage_path.exists():
      return {}
    try:
      with self.storage_path.open(encoding="utf-8") as file:
        data = json.load(file)
      if (not isinstance(data, dict)
          or data.get("version") != DATA_VERSION
          or not isinstance(data.get("inventories"), dict)):
        raise ValueError("unsupported or malformed inventory data")

      inventories = {}
      for raw_id, inventory_data in data["inventories"].items():
        if not isinstance(raw_id, str) or not raw_id.isdecimal():
          raise ValueError("inventory user IDs must be numeric strings")
        inventories[int(raw_id)] = UserInventory.from_data(inventory_data)
      return inventories
    except (OSError, json.JSONDecodeError, ValueError) as error:
      raise InventoryPersistenceError(
        f"Cannot load saved inventories from {self.storage_path}: {error}"
      ) from error

  def _save_inventory(self):
    data = {
      "version": DATA_VERSION,
      "inventories": {
        str(user_id): inventory.to_data()
        for user_id, inventory in sorted(self.allInventory.items())
      },
    }
    temporary_path = self.storage_path.with_name(
      f".{self.storage_path.name}.{os.getpid()}.tmp"
    )
    try:
      self.storage_path.parent.mkdir(parents=True, exist_ok=True)
      with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
      os.replace(temporary_path, self.storage_path)
    except OSError as error:
      temporary_path.unlink(missing_ok=True)
      raise InventoryPersistenceError(
        f"Cannot save inventories to {self.storage_path}: {error}"
      ) from error


  def _add(self, user, item):
    self._inv(user).add(item)
    self._save_inventory()

  def _remove(self, user, item):
    user_id = self._user_id(user)
    if user_id in self.allInventory:
      inventory = self.allInventory[user_id]
      if inventory.has(item):
        inventory.remove(item)
        if inventory.isEmpty():
          del self.allInventory[user_id]
        self._save_inventory()

  def _inv(self, user):
    user_id = self._user_id(user)
    if user_id in self.allInventory:
      return self.allInventory[user_id]
    else:
      inv = UserInventory()
      self.allInventory[user_id] = inv
      return inv


  @commands.command()
  async def give(self, ctx, user: discord.Member, item: str):
    """'^give @user item': create and give <item> to <user>"""
    if user and item:
      item = single(self.inflector, item)
      log.info(f"Giving {item} to {user}")
      inv = self._inv(user)
      if not inv.has(item):
        inv.add(item)
        if user == self.bot.user:
          # bot puts everything in pockets
          inv.pocket(item)
        self._save_inventory()
        if user == self.bot.user:
          # if item=='nothing' say 'thanks for nothing'
          if item.lower() == "nothing":
            await ctx.reply("Thanks for nothing.")
          else:
            await ctx.reply("Thank you!")
        else:
          #await ctx.channel.send(f"{ctx.author.mention} gave {self.inflector.a(item)} to {user.mention}.")
          await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
      else:
        if user == self.bot.user:
          #await ctx.channel.send("No thank you.")
          await ctx.reply("No thanks, mrwelch is independently wealchy.")
        else:
          await ctx.reply(f"Too many of those floating around.")

  @commands.command()
  async def take(self, ctx, item: str):
    """find all people with <item>, pick one at random, take it from them"""
    if item:
      item = single(self.inflector, item)
      victims = [user_id for user_id, inventory in self.allInventory.items()
                 if inventory.see(item)]
      if victims:
        victim_id = random.choice(victims)
        victim_inventory = self.allInventory[victim_id]
        victim_inventory.remove(item)
        if victim_inventory.isEmpty():
          del self.allInventory[victim_id]
        self._inv(ctx.author).add(item)
        self._save_inventory()
        guild = getattr(ctx, "guild", None)
        member = guild.get_member(victim_id) if guild else None
        user = member or self.bot.get_user(victim_id)
        victim_name = user.name if user else f"user {victim_id}"
        resp = f"You \"found\" {victim_name}'s {item}!"
      else:
        resp = f"You don't see any {item}."
      await ctx.reply(resp)

  @commands.command()
  async def drop(self, ctx, item: str):
    """delete the <item> if you have it"""
    if item:
      item = single(self.inflector, item)
      user = ctx.author
      user_id = self._user_id(user)
      if user_id in self.allInventory:
        inv = self.allInventory[user_id]
        if inv.has(item):
          self._remove(user, item)
          await ctx.reply("Dropped.")

  @commands.command()
  async def use(self, ctx, item: str):
    """use (and delete) the <item>"""
    if item:
      item = single(self.inflector, item)
      user = ctx.author
      user_id = self._user_id(user)
      if user_id in self.allInventory:
        inv = self.allInventory[user_id]
        if inv.has(item):
          self._remove(user, item)
          await ctx.reply(f"You drank the {item}.")

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
    user_id = self._user_id(user)
    if user_id in self.allInventory:
      desc = self.allInventory[user_id].describe()
    if not desc:
      desc = "nothing, and should be ashamed"
    await ctx.reply(f"{intro} {desc}.")

  @commands.command()
  async def pocket(self, ctx, item: str):
    """hide <item> from other users"""
    resp = None
    if item:
      inv = self.allInventory.get(self._user_id(ctx.author))
      if not inv or inv.isEmpty():
        #resp = "You have nothing."
        await ctx.message.add_reaction("\N{SHRUG}") #("\N{NO ENTRY}")
      elif not inv.has(item):
        #resp = "You don't have that."
        await ctx.message.add_reaction("\N{SHRUG}")
      else:
        inv.pocket(item)
        self._save_inventory()
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
      if resp: await ctx.reply(resp)

  @commands.command(hidden=True)
  async def reboot(self, ctx):
    await ctx.reply("Who do you think you are?!")



async def setup(bot):
  await bot.add_cog(InventoryCog(
    bot,
    storage_path=getattr(bot, "inventory_path", None),
  ))



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
