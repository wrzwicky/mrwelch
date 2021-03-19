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

def rando() -> str:
  if random.random() >= 0.90:
    # Secret quote from Critical Role
    q = "And now this news break from Critical Role:\n" + random.choice(critrole) + "\nThat is all."
  else:
    n = random.randrange(len(mrwelch))
    q = "%d. %s" % (n, mrwelch[n])
  return q


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

p = os.path.join(sys.path[0], "critrole.txt")
critrole = []
with open(p,"r") as f:
  for line in f:
    critrole.append(line.strip())

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
	"mrwelch": mrwelch,
	"critrole": critrole
}

simple = simpleeval.EvalWithCompoundTypes(functions=funs, names=vars)

wait_for_internet_connection()

bot = commands.Bot(
	command_prefix="😈",  # Change to desired prefix
	case_insensitive=True,  # Commands aren't case-sensitive
  description="mr welch"
)

bot.author_id = os.environ.get("DISCORD_AUTHOR_ID")


def reparse2(message: discord.Message) -> List:
  """
  Parse message content, alternating strings and User/Role/TextChannel objects.
  Roles and channels are looked up in the server from whence came the message.
  All strings are stripped; empty strings are dropped.
  """
  # user mentions: <@-id-> or <@!-id->
  #  - <@ for user, <@! if user has nick
  # role mentions: <@&-id->
  # chan mentions: <#-id->
  mx = re.compile("<(@|@!|@&|#)(\d+)>")
  msg = message.content
  ans = []
  while True:
    # find next mention
    m = mx.search(msg)
    if not m:
      break
    # append text (if not blank)
    if m.start() > 0:
      t = msg[:m.start()].strip()
      if t:
        ans.append(t)
    # convert and append mention
    all = m[0]
    typ = m[1]
    id  = int(m[2])
    if typ == '@' or typ == '@!':
      obj = bot.get_user(id)
    elif typ == '@&':
      obj = message.guild.get_role(id)
    elif typ == '#':
      obj = message.guild.get_channel(id)
    else:
      log.error(f"unrecognized mention type '{typ}' for id {id}")
      obj = all
    ans.append(obj)

    # loop with remainder of string
    msg = msg[m.end():]

  t = msg.strip()
  if t:
    ans.append(t)
  return ans


@bot.event 
async def on_ready():
  log.info("I'm in as "+str(bot.user))
  log.info(rando())


@bot.event
async def on_guild_join(guild):
    # Send a Hello only to 'general' channel, if exists.
    general = discord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send('Hello %s! I like to mock Mr. Welch. @mention me to get a random message; or @mention me with a number or some text for a specific message.' % (guild.name))


@bot.event
async def on_message(msg: discord.Message):
  """take commands only from messages that @mention me"""
  #msg .channel:Union[abc.Messageable] .author:Member .mentions:List[Member] .created_at:datetime.datetime(UTC) .content:str

  if msg.author == bot.user:
    log.info("(my own response)")
  else:
    # parse out <@id> mentions
    #  -msg.mentions includes bot.user if someone replies to bot
    objmsg = reparse2(msg)
    m = ' '.join(s for s in objmsg if isinstance(s, str))
    userMents = set(u for u in objmsg if isinstance(u, discord.User) or isinstance(u, discord.ClientUser))
    roleMents = set(u for u in objmsg if isinstance(u, discord.Role))

    # find my role in the server sending the message
    #  -On the site, bots clearly have roles, but I can't get any API to return the role.
    #   botrole = msg.guild.get_member(bot.user.id).role -- no attribute 'role'
    myroles = set()
    for r in msg.guild.roles:
      #print(f" - {r.name}: {r.members}")
      if r.name == "@everyone":
        continue
      if bot.user in r.members:
        myroles.add(r)
    #print(f"myroles: {myroles}") ## success!


    # a little tracing
    if bot.user in msg.mentions and not bot.user in userMents:
      log.info(f"({msg.author.name} replied to me)")

    # bail if msg not for me
    if not bot.user in userMents and not myroles & roleMents:
      return

    log.info(f"{msg.created_at} : {msg.author.name} -> {msg.guild.name} #{msg.channel.name}\n  {msg.content}")


    if m:
      if m == "crro":
        await msg.channel.send(random.choice(critrole))
        return

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
          # math expression? evaluate
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
          # else text search
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


if __name__ == '__main__':  # Ensures this is the file being ran
  token = os.environ.get("DISCORD_BOT_SECRET")
  bot.run(token)  # Starts the bot
