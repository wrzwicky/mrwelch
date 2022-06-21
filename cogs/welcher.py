#!/usr/bin/env python3
import logging
import math, os, random, re, sys, time, urllib
from typing import List, Tuple
from dotenv import load_dotenv

import simpleeval
import discord, discord.utils
from discord.ext import commands
from user_inventory import *
from magic8 import *

log = logging.getLogger('mrwelch')
idunno = Magic8Ball()

def loadMrwelch(fil): #-> {int -> str}
  mrwelch = {}
  with open(fil, "r") as f:
    rx = re.compile("^(\d+)\.\s*(.*)$")
    for line in f:
      line = line.strip()
      if not line.startswith("#"):
        (num,msg) = rx.match(line).groups()
        mrwelch[int(num)] = msg
  return mrwelch

def reparse2(bot: commands.Bot, message: discord.Message) -> List:
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



class WelchCog(commands.Cog, name="mrwelch"):
  """Things Mr. Welch is not allowed to do"""

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

  def __init__(self, bot):
    self.bot = bot

    p = os.path.join(sys.path[0], "mrwelch.txt")
    mrwelch = loadMrwelch(p)

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

    log.info(f"{len(mrwelch) + len(critrole)} snarks loaded")

    self.mrwelch = mrwelch
    self.critrole = critrole

    # ----------

    def shuffled(thing):
      if isinstance(thing,str):
        return "".join(random.sample(thing,len(thing)))
      elif isinstance(thing,(list,tuple)):
        return random.sample(thing,len(thing))
      else:
        raise simpleeval.FeatureNotAvailable("shuffle "+type(thing))

    # DEFAULT_FUNCTIONS provides randint(x) rand() int(x) float(x) str(x)
    simpleeval.MAX_POWER = 9999
    funs = simpleeval.DEFAULT_FUNCTIONS.copy()
    funs.update({
        'abs' : abs, 'all' : all, 'any' : any, 'ascii' : ascii, 'chr' : chr, 'complex' : complex, 'copyright' : copyright, 'credits' : credits, 'divmod' : divmod, 'filter' : filter, 'format' : format, 'hash' : hash, 'hex' : hex, 'len' : len, 'license' : license, 'max' : max, 'min' : min, 'oct' : oct, 'ord' : ord, 'pow' : pow, 'range' : range, 'reversed' : reversed, 'round' : round, 'sorted' : sorted, 'sum' : sum, 'zip' : zip,

        'sin' : math.sin,
        'cos' : math.cos,

        'shuffle' : shuffled,
        'sample'  : random.sample,
        'choice'  : random.choice,
        'choices' : random.choices,
    })
    vars = {
      "mrwelch": self.mrwelch.values(),
      "critrole": self.critrole
    }

    self.eval = simpleeval.EvalWithCompoundTypes(functions=funs, names=vars)

  def rando(self) -> str:
    if random.random() >= 0.90:
      # Secret quote from Critical Role
      q = "And now this news break from Critical Role:\n" + random.choice(self.critrole) + "\nThat is all."
    else:
      n = random.randrange(len(self.mrwelch))
      q = "%d. %s" % (n, self.mrwelch[n])
    return q


  @commands.Cog.listener()
  async def on_ready(self):
    log.info(self.rando())


  @commands.Cog.listener()
  async def on_message(self, msg: discord.Message):
    """take commands only from messages that @mention me"""
    #msg .channel:Union[abc.Messageable] .author:Member .mentions:List[Member] .created_at:datetime.datetime(UTC) .content:str

    #log.info(f"{msg.created_at} : {msg.author.name} -> {msg.guild.name} #{msg.channel.name}\n  {msg.content}")

    if msg.content.startswith(self.bot.command_prefix):
      return
    if msg.author == self.bot.user:
      log.info("(my own response)")
      return

    # I believe the problem is this: message.mentions is intended to contain @mentions, but in reality it also includes the bot if some responds to it. So I have to re-parse the raw text message, filter out the actual mentions, and make decisions from that.

    # parse out <@id> mentions
    #  -msg.mentions includes bot.user if someone replies to bot
    objmsg = reparse2(self.bot, msg)
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
      if self.bot.user in r.members:
        myroles.add(r)
    #print(f"myroles: {myroles}") ## success!


    # a little tracing
    if self.bot.user in msg.mentions and not self.bot.user in userMents:
      log.info(f"({msg.author.name} replied to me)")

    # bail if msg not for me
    if not self.bot.user in userMents and not myroles & roleMents:
      return

    log.info(f"{msg.created_at} : {msg.author.name} -> {msg.guild.name} #{msg.channel.name}\n  {msg.content}")


    if m:
      if m == "crro":
        await msg.channel.send(random.choice(self.critrole))
        return

      try:
        # lone integer? use as index
        i = int(m)
        if i == 1984:
          await msg.channel.send("Sorry, this one is not about 1984.")
        elif i in self.mrwelch:
          await msg.channel.send("%d. %s" % (i, self.mrwelch[i]))
        else:
          await msg.channel.send("Mr. Welch is not so experienced just yet.")
      except ValueError:
        log.info(" -> not a number")
        try:
          # math expression? evaluate
          ans = self.eval.eval(m)
          if isinstance(ans, (int,float)):
            await msg.channel.send("Maybe like " + str(ans))
          elif isinstance(ans, (list, dict, tuple, complex)):
            await msg.channel.send(str(ans))
          else:
            raise TypeError("Not a type I print: "+str(ans))
        except self.REFUSERS as e:
          log.info(" -> refused eval: "+repr(e))
          await msg.channel.send("Nah.")
        except:
          # else text search
          t,e,tb = sys.exc_info()
          log.info(" -> not math "+repr(e))
          m = m.lower()
          ix = [k for k in self.mrwelch if m in self.mrwelch[k].lower()]
          if len(ix) > 0:
            i = random.choice(ix)
            await msg.channel.send("%d. %s" % (i, self.mrwelch[i]))
          else:
            #await msg.channel.send("Mr. Welch has not encountered such a thing.")
            await msg.channel.send(idunno.rando())
    else:
      await msg.channel.send(self.rando())


def setup(bot):
	bot.add_cog(WelchCog(bot))
