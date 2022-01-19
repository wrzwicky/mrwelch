# Copied from:
# nonchris/discord-custom-help-command.py
# https://gist.github.com/nonchris/1c7060a14a9d94e7929aa2ef14c41bc2

import discord
from discord.ext import commands
from discord.errors import Forbidden


PAID_PLACEMENTS = {
  "help": (
    "Hamburger Helper-Helper helps your Hamburger Helper help you help make a great meal.",
    "sponsored by Fuji Chemicals"
  )
}

async def send_embed(ctx, embed):
    try:
        await ctx.send(embed=embed)
    except Forbidden:
        try:
            await ctx.send("Hey, seems like I can't send embeds. Please check my permissions :)")
        except Forbidden:
            await ctx.author.send(
                f"Hey, seems like I can't send any message in {ctx.channel.name} on {ctx.guild.name}\n"
                f"May you inform the server team about this issue? :slight_smile: ", embed=embed)


def spell_cogs(bot):
  words = {}
  for cog in bot.cogs:
    words[cog.lower()] = bot.cogs[cog].__doc__

    for command in bot.get_cog(cog).get_commands():
      if not command.hidden:
        words[command.name.lower()] = command.help

  return words


class HelpCog(commands.Cog):
    """print some help"""

    def __init__(self, bot):
        self.bot = bot

      	# !SET THOSE VARIABLES TO MAKE THE COG FUNCTIONAL!
        self.version = "v2021.01.17.76.7"
	
        # setting owner name - if you don't wanna be mentioned remove line 49-60 and adjust help text (line 88) 
        self.owner = "DISCORD-ID"
        self.owner_id = "USERNAME#1234"


    @commands.command()
    # @commands.bot_has_permissions(add_reactions=True,embed_links=True)
    async def help(self, ctx, *input):
      """print some help"""

      words = spell_cogs(self.bot)

      if not input:
        #await ctx.message.add_reaction("\N{SHRUG}")
        emb = discord.Embed(
          title='Help',
          color=discord.Color.blue(),
          description = " ".join(sorted(words))
        )

        # for w in words:
        #   emb.add_field(name=w, value=words[w])

        await send_embed(ctx, emb)

      elif len(input) > 1:
        await ctx.message.add_reaction("😩")

      else:
        w = input[0].lower()
        
        if w in PAID_PLACEMENTS:
          emb = discord.Embed(
            title=input[0],
            color=discord.Color.random(),
            description = PAID_PLACEMENTS[w][0]
          )
          emb.set_footer(text=PAID_PLACEMENTS[w][1])
          await send_embed(ctx, emb)

        elif w in words:
          emb = discord.Embed(
            title = input[0],
            color = discord.Color.green(),
            description = words[w]
          )
          await send_embed(ctx, emb)

        else:
          await ctx.message.add_reaction("\N{SHRUG}")




def setup(bot):
    bot.remove_command('help')
    bot.add_cog(HelpCog(bot))
