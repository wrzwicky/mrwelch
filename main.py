#!/usr/bin/env python3
import logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger('mrwelch')
log.setLevel(logging.INFO) #DEBUG)
# discord.py dumps stuff to DEBUG

import os, random, re, sys, time, urllib
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

def wait_for_internet_connection():
  while True:
    try:
      print('probing discord ...')
      url = 'https://discord.com/'
      req = urllib.request.Request(url, headers={'User-Agent' : "Magic Browser"}) 
      response = urllib.request.urlopen(req, timeout=1)
      print(' -> is up!')
      return
    except urllib.error.URLError as e:
      if e.code:
        print(' -> bad query, but is up:', e)
        return
      else:
        print(' -failed', e.code)
        time.sleep(2)



random.seed()
if not os.environ.get("DISCORD_AUTHOR_ID"):
  load_dotenv()
  if not os.environ.get("DISCORD_AUTHOR_ID"):
    print("Please create .env file with DISCORD_AUTHOR_ID and DISCORD_BOT_SECRET.")
    sys.exit(5)

wait_for_internet_connection()

bot = commands.Bot(
	command_prefix="^",  # Change to desired prefix
	case_insensitive=True,  # Commands aren't case-sensitive
  description="Things Mr. Welch is no longer allowed to do in D&D."
)

bot.author_id = os.environ.get("DISCORD_AUTHOR_ID")


@bot.event 
async def on_ready():
  log.info("I'm in as "+str(bot.user))


@bot.event
async def on_guild_join(guild):
    # Send a Hello only to 'general' channel, if exists.
    general = discord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send('Hello %s! I like to mock Mr. Welch. @mention me to get a random message; or @mention me with a number or some text for a specific message.' % (guild.name))



if __name__ == '__main__':
  bot.load_extension('cogs.inventory')
  bot.load_extension('cogs.welcher')

  token = os.environ.get("DISCORD_BOT_SECRET")
  bot.run(token)  # Starts the bot
