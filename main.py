#!/usr/bin/env python3
import logging

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger("mrwelch")
log.setLevel(logging.INFO)  # DEBUG)
# discord.py dumps stuff to DEBUG

import argparse
import asyncio
import os, random, re, sys
import simpleeval
from typing import List, Tuple
from dotenv import load_dotenv

import discord, discord.utils
from discord.ext import commands


##
## "Things Mr. Welch is not allowed to do" bot for Discord
## mention @mrwelch for random quote
## or mention with nubmer for that exact quote
## or mention with string for random quote containing string
## or mention with Python expression for braining
##
## Create file ".env" with secret keys:
##   DISCORD_AUTHOR_ID
##   DISCORD_BOT_ID
##   DISCORD_BOT_SECRET
##
## https://discordpy.readthedocs.io/en/latest/api.html
## https://discord.com/api/oauth2/authorize?client_id=773455562338992159&permissions=2048&scope=bot
##

random.seed()
load_dotenv()

EXTENSIONS = (
    "cogs.inventory",
    "cogs.welcher",
    "cogs.define",
    "cogs.dice",
    "cogs.story",
    "cogs.helphelp",
)


class WelchBot(commands.Bot):
    async def setup_hook(self):
        for extension in EXTENSIONS:
            await self.load_extension(extension)


intents = discord.Intents.default()
intents.message_content = True
bot = WelchBot(
    command_prefix="^",  # Change to desired prefix
    case_insensitive=True,  # Commands aren't case-sensitive
    intents=intents,
    description="Things Mr. Welch is no longer allowed to do in D&D.",
)

bot.author_id = os.environ.get("DISCORD_AUTHOR_ID")


@bot.event
async def on_ready():
    log.info("I'm in as " + str(bot.user))


@bot.event
async def on_guild_join(guild):
    # Send a Hello only to 'general' channel, if exists.
    general = discord.utils.find(lambda x: x.name == "general", guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send(
            "Hello %s! I like to mock Mr. Welch. @mention me to get a random message; or @mention me with a number or some text for a specific message."
            % (guild.name)
        )


async def check_startup():
    async with bot:
        await bot.setup_hook()
        print(f"Startup check passed: {len(bot.cogs)} cogs loaded.")
        print("Commands: " + ", ".join(sorted(c.name for c in bot.commands)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=bot.description)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Load all commands without connecting to Discord",
    )
    args = parser.parse_args()
    if args.check:
        asyncio.run(check_startup())
    else:
        required = ("DISCORD_AUTHOR_ID", "DISCORD_BOT_SECRET")
        missing = [key for key in required if not os.environ.get(key, "").strip()]
        if missing:
            sys.exit("Missing Replit Secrets: " + ", ".join(missing))
        if not os.environ["DISCORD_AUTHOR_ID"].isdecimal():
            sys.exit("DISCORD_AUTHOR_ID must be your numeric Discord user ID.")
        try:
            bot.run(os.environ["DISCORD_BOT_SECRET"])
        except discord.LoginFailure:
            sys.exit(
                "Discord rejected DISCORD_BOT_SECRET. Update the bot token in Replit Secrets."
            )
        except discord.PrivilegedIntentsRequired:
            sys.exit(
                "Enable Message Content Intent on the Bot page in the Discord Developer Portal."
            )
