#!/usr/bin/env python3
import json
import logging
import os
import random
import tempfile
from pathlib import Path

import discord
from discord.ext import commands
import inflect

from user_inventory import UserInventory

log = logging.getLogger("mrwelch")

DATA_VERSION = 1
DEFAULT_STORAGE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "inventories.json"
)


class InventoryPersistenceError(RuntimeError):
    """Raised when saved inventory data cannot safely be loaded or written."""


def single(p, noun):
    """Patch inflect's singularizer so already-singular nouns stay unchanged."""
    s = p.singular_noun(noun)
    if s:
        return s
    else:
        return noun


class InventoryCog(commands.Cog):
    """Weird little per-user inventory keeper"""

    def __init__(self, bot, storage_path=None):
        self.bot = bot
        configured_path = (
            storage_path
            or getattr(bot, "inventory_path", None)
            or getattr(bot, "inventory_data_file", None)
            or DEFAULT_STORAGE_PATH
        )
        self.storage_path = Path(configured_path)
        self.inflector = inflect.engine()
        self.allInventory = self._load_inventory()

    @staticmethod
    def _user_id(user):
        """Return a stable Discord ID for a member, user, or stored ID."""
        return user if isinstance(user, int) else int(user.id)

    def _load_inventory(self):
        """Load and validate saved inventories; never replace an unreadable file."""
        try:
            with self.storage_path.open(encoding="utf-8") as saved_file:
                data = json.load(saved_file)

            if (
                not isinstance(data, dict)
                or set(data) != {"version", "inventories"}
                or type(data["version"]) is not int
                or data["version"] != DATA_VERSION
                or not isinstance(data["inventories"], dict)
            ):
                raise ValueError("unsupported or malformed inventory data")

            inventories = {}
            for raw_id, inventory_data in data["inventories"].items():
                if (
                    not isinstance(raw_id, str)
                    or not raw_id.isdecimal()
                    or int(raw_id) <= 0
                ):
                    raise ValueError(
                        "inventory user IDs must be positive numeric strings"
                    )
                inventories[int(raw_id)] = UserInventory.from_data(inventory_data)
            return inventories
        except FileNotFoundError:
            # A missing file is the normal first-run state.
            return {}
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise InventoryPersistenceError(
                f"Cannot load saved inventories from {self.storage_path}: {error}"
            ) from error

    def _save_inventory(self):
        """Atomically save inventories keyed by Discord ID."""
        data = {
            "version": DATA_VERSION,
            "inventories": {
                str(user_id): inventory.to_data()
                for user_id, inventory in sorted(self.allInventory.items())
            },
        }
        temporary_path = None
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.storage_path.parent,
                prefix="inventory-",
                suffix=".tmp",
                delete=False,
            ) as saved_file:
                temporary_path = Path(saved_file.name)
                json.dump(
                    data, saved_file, ensure_ascii=False, indent=2, sort_keys=True
                )
                saved_file.write("\n")
                saved_file.flush()
                os.fsync(saved_file.fileno())
            os.replace(temporary_path, self.storage_path)
        except (OSError, UnicodeError) as error:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    log.exception(
                        "Could not remove incomplete inventory file %s", temporary_path
                    )
            raise InventoryPersistenceError(
                f"Cannot save inventories to {self.storage_path}: {error}"
            ) from error

    def _add(self, user, item):
        self._inv(user).add(item)
        self._save_inventory()

    def _remove(self, user, item):
        user_id = self._user_id(user)
        inventory = self.allInventory.get(user_id)
        if inventory and inventory.has(item):
            inventory.remove(item)
            if inventory.isEmpty():
                del self.allInventory[user_id]
            self._save_inventory()

    def _inv(self, user):
        user_id = self._user_id(user)
        if user_id not in self.allInventory:
            self.allInventory[user_id] = UserInventory()
        return self.allInventory[user_id]

    @commands.command()
    async def give(self, ctx, user: discord.Member, item: str):
        """'^give @user item': create and give <item> to <user>"""
        if user and item:
            item = single(self.inflector, item)
            log.info("Giving %s to %s", item, user)
            inventory = self._inv(user)
            if not inventory.has(item):
                inventory.add(item)
                if user == self.bot.user:
                    # The bot puts everything in pockets.
                    inventory.pocket(item)
                self._save_inventory()

                if user == self.bot.user:
                    if item.lower() == "nothing":
                        await ctx.reply("Thanks for nothing.")
                    else:
                        await ctx.reply("Thank you!")
                else:
                    await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
            elif user == self.bot.user:
                await ctx.reply("No thanks, mrwelch is independently wealchy.")
            else:
                await ctx.reply("Too many of those floating around.")

    @commands.command()
    async def take(self, ctx, item: str):
        """find all people with <item>, pick one at random, take it from them"""
        if item:
            item = single(self.inflector, item)
            victims = [
                user_id
                for user_id, inventory in self.allInventory.items()
                if inventory.see(item)
            ]
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
                resp = f'You "found" {victim_name}\'s {item}!'
            else:
                resp = f"You don't see any {item}."
            await ctx.reply(resp)

    @commands.command()
    async def drop(self, ctx, item: str):
        """delete the <item> if you have it"""
        if item:
            item = single(self.inflector, item)
            user_id = self._user_id(ctx.author)
            inventory = self.allInventory.get(user_id)
            if inventory and inventory.has(item):
                self._remove(ctx.author, item)
                await ctx.channel.send("Dropped.")

    @commands.command()
    async def use(self, ctx, item: str):
        """use (and delete) the <item>"""
        if item:
            item = single(self.inflector, item)
            user_id = self._user_id(ctx.author)
            inventory = self.allInventory.get(user_id)
            if inventory and inventory.has(item):
                self._remove(ctx.author, item)
                await ctx.channel.send(f"You drank the {item}.")

    @commands.command(aliases=["i"])
    async def inventory(self, ctx, user: discord.Member = None):
        """list all items you or <user> possess"""
        if not user:
            user = ctx.author
            intro = "You have"
        elif user == self.bot.user:
            intro = "I have"
        else:
            intro = user.mention + " has"

        inventory = self.allInventory.get(self._user_id(user))
        description = inventory.describe() if inventory else ""
        await ctx.reply(f"{intro} {description or 'nothing and should be ashamed'}.")

    @commands.command()
    async def pocket(self, ctx, item: str):
        """hide <item> from other users"""
        if item:
            inventory = self.allInventory.get(self._user_id(ctx.author))
            if not inventory or inventory.isEmpty() or not inventory.has(item):
                await ctx.message.add_reaction("\N{SHRUG}")
            else:
                inventory.pocket(item)
                self._save_inventory()
                await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(hidden=True)
    async def reboot(self, ctx):
        await ctx.reply("Who do you think you are?!")


async def setup(bot):
    await bot.add_cog(
        InventoryCog(
            bot,
            storage_path=getattr(bot, "inventory_path", None),
        )
    )


# TODO
# if 'item' is plural, command should affect all
# allow private ^i
# use collections.Counter in user_inventory
# what if extra args?
# what if item is user or guild etc?
# if user give gun to mrwelch, "mrwelch uses gun to take everything from user"
# private DM with full inventory
# use reactions instead of text
# if item=='nothing', don't give, maybe reaction=confusion
