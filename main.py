import os, random, re, sys
from typing import List, Tuple
from keep_alive import keep_alive
from discord.ext import commands
import discord.utils

##
## "Things Mr. Welch is not allowed to do" bot for Discord
## mention @mrwelch for random quote
## or mention with number for that exact quote
## or mention with string for random quote containing string
## or mention with some simple Python code to evaluate that code
##
## Create file ".env" with secret keys:
##   DISCORD_AUTHOR_ID
##   DISCORD_BOT_SECRET
##
## https://discordpy.readthedocs.io/en/latest/api.html
## https://discord.com/api/oauth2/authorize?client_id=773455562338992159&permissions=2048&scope=bot
##

random.seed()
if not os.environ.get("DISCORD_AUTHOR_ID"):
  print("Please create .env file with DISCORD_AUTHOR_ID and DISCORD_BOT_SECRET.")
  sys.exit(5)


mrwelch = {}
with open("mrwelch.txt", "r") as f:
  rx = re.compile("^(\d+)\.\s*(.*)$")
  for line in f:
    (num,msg) = rx.match(line).groups()
    mrwelch[int(num)] = msg

def rando() -> str:
  n = random.randrange(len(mrwelch))
  return "%d. %s" % (n, mrwelch[n])

def reparse(msg: str) -> List[str]:
  """parse message content, alternating strings and coded mentions"""
  mx = re.compile("<@!?(\d+)>")
  ans = []
  while True:
    m = mx.search(msg)
    if not m:
      break
    if m.start() > 0:
      ans.append(msg[:m.start()].strip())
    ans.append(m[0])
    msg = msg[m.end():]
  if msg:
    ans.append(msg.strip())
  return ans


bot = commands.Bot(
	command_prefix="😈",  # Change to desired prefix
	case_insensitive=True,  # Commands aren't case-sensitive
  description="mr welch"
)

bot.author_id = os.environ.get("DISCORD_AUTHOR_ID")

@bot.event 
async def on_ready():
  print("I'm in as", bot.user)
  print(rando())

@bot.command()
async def r(ctx):
  await ctx.send(rando())

@bot.command()
async def n(ctx, n:int):
  await ctx.send("%d. %s" % (n, mrwelch[n]))

@bot.command()
async def s(ctx, s:str):
  s = s.lower()
  ix = [k for k in mrwelch if s in mrwelch[k].lower()]
  if len(ix) > 0:
    n = random.choice(ix)
    await ctx.send("%d. %s" % (n, mrwelch[n]))


@bot.event
async def on_guild_join(guild):
    general = discord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send('Hello! I like to mock Mr. Welch. @mention me to get a random message; or @mention me with a number or some text for a specific message.'.format(guild.name))

@bot.event
async def on_message(msg):
  """take commands only from messages that @mention me"""
  #msg .channel .author .mentions
  if msg.author is not bot.user and bot.user in msg.mentions:
    # purge <@code> mentions
    r = reparse(msg.content)
    m = ' '.join([s for s in r if not s.startswith("<@")])

    if m:
      try:
        i = int(m)
        if i in mrwelch:
          await msg.channel.send("%d. %s" % (i, mrwelch[i]))
        else:
          await msg.channel.send("Mr. Welch is not so experienced just yet.")
      except ValueError:
        m = m.lower()
        ix = [k for k in mrwelch if m in mrwelch[k].lower()]
        if len(ix) > 0:
          i = random.choice(ix)
          await msg.channel.send("%d. %s" % (i, mrwelch[i]))
        else:
          await msg.channel.send("Mr. Welch has not encountered such a thing.")
    else:
      await msg.channel.send(rando())


extensions = [
#  'cogs.cog_example'  # Same name as it would be if you were importing it
]

if __name__ == '__main__':  # Ensures this is the file being ran
  for extension in extensions:
    bot.load_extension(extension)  # Loads every extension.

  keep_alive()  # Starts a webserver to be pinged.
  token = os.environ.get("DISCORD_BOT_SECRET")
  bot.run(token)  # Starts the bot
