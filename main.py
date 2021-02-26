import logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger('mrwelch')
log.setLevel(logging.DEBUG)
# discord.py dumps stuff to DEBUG

import os, random, re, sys, time, urllib
import simpleeval
from typing import List, Tuple
from dotenv import load_dotenv

import discord.utils
from discord.ext import commands

##
## "Things Mr. Welch is not allowed to do" bot for Discord
## mention @mrwelch for random quote
## or mention with nubmer for that exact quote
## or mention with string for random quote containing string
## or mention with math expression for braining
##
## Create file ".env" with secret keys:
##   DISCORD_AUTHOR_ID
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

def rando() -> str:
  n = random.randrange(len(mrwelch))
  return "%d. %s" % (n, mrwelch[n])

def reparse(msg: str) -> List[str]:
  """parse message content, alternating strings and coded mentions"""
  # user mentions: <@-id-> or <@!-id->
  # role mentions: <@&-id->
  # chan mentions: <#-id->
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


random.seed()
if not os.environ.get("DISCORD_AUTHOR_ID"):
  load_dotenv()
  if not os.environ.get("DISCORD_AUTHOR_ID"):
    print("Please create .env file with DISCORD_AUTHOR_ID and DISCORD_BOT_SECRET.")
    sys.exit(5)

mrwelch = {}
p = os.path.join(sys.path[0], "mrwelch.txt")
with open(p, "r") as f:
  rx = re.compile("^(\d+)\.\s*(.*)$")
  for line in f:
    (num,msg) = rx.match(line).groups()
    mrwelch[int(num)] = msg

p = os.path.join(sys.path[0], "shane.txt")
with open(p, "r") as f:
  num = max(mrwelch.keys())
  for line in f:
    num += 1
    mrwelch[num] = line

log.info(f"{len(mrwelch)} snarks loaded")

# exceptions that prevent string search
REFUSERS = (
  discord.errors.HTTPException,
#  simpleeval.AttributeDoesNotExist,
  simpleeval.FeatureNotAvailable,
#  simpleeval.FunctionNotDefined,
#  simpleeval.InvalidExpression,
  simpleeval.IterableTooLong,
#  simpleeval.NameNotDefined,
  simpleeval.NumberTooHigh,
  OverflowError,
#  TypeError
)


def shuffled(thing):
	if isinstance(thing,str):
		return "".join(random.sample(thing,len(thing)))
	elif isinstance(thing,list):
		return random.sample(thing,len(thing))
	else:
		raise simpleeval.FeatureNotAvailable("shuffle "+type(thing))

# DEFAULT_FUNCTIONS provides randint(x) rand() int(x) float(x) str(x)
simpleeval.MAX_POWER = 9999
funs = simpleeval.DEFAULT_FUNCTIONS.copy()
funs.update(
	shuffle=shuffled,
	sample=random.sample,
	choice=random.choice,
	choices=random.choices,
	range=range
)
vars = {
	"mrwelch": mrwelch
}

simple = simpleeval.EvalWithCompoundTypes(functions=funs, names=vars)

wait_for_internet_connection()

bot = commands.Bot(
	command_prefix="😈",  # Change to desired prefix
	case_insensitive=True,  # Commands aren't case-sensitive
  description="mr welch"
)

bot.author_id = os.environ.get("DISCORD_AUTHOR_ID")

@bot.event 
async def on_ready():
  log.info("I'm in as "+str(bot.user))
  log.info(rando())

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
    # Send a Hello only to 'general' channel, if exists.
    general = discord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send('Hello %s! I like to mock Mr. Welch. @mention me to get a random message; or @mention me with a number or some text for a specific message.' % (guild.name))

@bot.event
async def on_message(msg):
  """take commands only from messages that @mention me"""
  #msg .channel:Union[abc.Messageable] .author:Member .mentions:List[Member] .created_at:datetime.datetime(UTC) .content:str

  if msg.author == bot.user:
    log.info("(my own response)")
  elif bot.user in msg.mentions:
	# or '' in msg.role_mentions:
	# -- bots don't officially have roles, even though a role is shown in Discord
    log.info(f"{msg.created_at} : {msg.author.name} : {msg.clean_content}")

    # purge <@code> mentions
    r = reparse(msg.content)
    m = ' '.join([s for s in r if not s.startswith("<@")])

    if m:
      try:
        # lone integer? use as index
        i = int(m)
        if i == 1984:
          await msg.channel.send("Sorry, this one is not about 1984.")
        elif i in mrwelch:
          await msg.channel.send("%d. %s" % (i, mrwelch[i]))
        else:
          await msg.channel.send("Mr. Welch is not so experienced just yet.")
      except ValueError:
        log.info(" -> not a number")
        try:
          # math expression?
          ans = simple.eval(m)
          if isinstance(ans,int):
            await msg.channel.send("Maybe like " + str(ans))
          elif isinstance(ans,float):
            await msg.channel.send("Maybe like " + str(ans))
          else:
            await msg.channel.send(str(ans))
        except REFUSERS as e:
          log.info(" -> refused eval: "+repr(e))
          await msg.channel.send("Nah.")
        except:
          # literal search
          t,e,tb = sys.exc_info()
          log.info(" -> not math "+repr(e))
          m = m.lower()
          ix = [k for k in mrwelch if m in mrwelch[k].lower()]
          if len(ix) > 0:
            i = random.choice(ix)
            await msg.channel.send("%d. %s" % (i, mrwelch[i]))
          else:
            await msg.channel.send("Mr. Welch has not encountered such a thing.")
    else:
      await msg.channel.send(rando())
  else:
    # other discussion; ignore
    #log.info(f"{msg.created_at} : {msg.author.name} : {msg.content}")
    pass


extensions = [
#  'cogs.cog_example'  # Same name as it would be if you were importing it
]

if __name__ == '__main__':  # Ensures this is the file being ran
  for extension in extensions:
    bot.load_extension(extension)  # Loads every extension.

  token = os.environ.get("DISCORD_BOT_SECRET")
  bot.run(token)  # Starts the bot
