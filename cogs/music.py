# Music bot using youtube_dl
# basic code from TCS student and coach

# TODO add reactions to embed to allow users to control song
# TODO add playlist support

## \N{name}
## https://www.fileformat.info/info/unicode/char/search.htm
# SPEAKER WITH CANCELLATION STROKE 🔇
# PUBLIC ADDRESS LOUDSPEAKER 📢
# SPEAKER	🔈
# SPEAKER WITH ONE SOUND WAVE	🔉
# SPEAKER WITH THREE SOUND WAVES 🔊
# NO ENTRY	⛔
# NO ENTRY SIGN	🚫
# THINKING FACE	🤔
# LEFT-POINTING MAGNIFYING GLASS	🔍
# RIGHT-POINTING MAGNIFYING GLASS	🔎

import logging
log = logging.getLogger('mrwelch')

import datetime
#import json
import discord
from discord.ext import commands
import youtube_dl

# replit packages -- add PyNaCl
# or "poetry add PyNaCl"


def parse_date(s):
  y = int(s[0:4])
  m = int(s[4:6])
  d = int(s[6:8])
  return datetime.datetime(y,m,d)


class MusicCog(commands.Cog):
  """Play music from YouTube into user's voice channel."""

  def __init__(self, bot):
    self.bot = bot

    self.YDL_OPTIONS = {
      'format':"bestaudio[ext=m4a]/bestaudio",
      'noplaylist': True,
      'default_search': 'auto',
      'cachedir': False  #needed to avoid weird 403 errors
    }
    self.FFMPEG_OPTIONS = {
      'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
      'options':'-vn'
    }

  @commands.command()
  async def join(self, ctx):
    """have mrwelch join user's voice channel"""
    if ctx.author.voice is None:
      await ctx.send("you are not in a voice channel")
    voice_channel=ctx.author.voice.channel
    if ctx.voice_client is None:
      await voice_channel.connect()
    else:
      await ctx.voice_client.move_to(voice_channel)

  
  @commands.command()
  async def leave(self, ctx):
    """have mrwelch disconnect from user's voice channel"""
    if ctx.voice_client:
      await ctx.voice_client.disconnect()
  

  @commands.command()
  async def play(self, ctx, *args):
    """find suitable video on YouTube, and play the audio in user's voice channel"""
    # get arg, note progress
    song = " ".join(args)
    log.info(f"Musiccing {song}")
    await ctx.message.add_reaction("🤔")

    # ensure we're in sender's voice channel
    if not ctx.voice_client:
      await self.join(ctx)
      if not ctx.voice_client:
        await ctx.message.remove_reaction("🤔", self.bot.user)
        await ctx.message.add_reaction("⛔")
        await ctx.send("unable to join voice channel")

    # stop current music
    ctx.voice_client.stop()

    # start youtube_dl
    ydl = youtube_dl.YoutubeDL(self.YDL_OPTIONS)
    info = ydl.extract_info(song, download=False)

    ## log findings -- need yes-playlist?
    # with open("_query_info.xml", 'w') as f:
    #   json.dump(info, f, indent=4)
    # for e in info['entries']:
    #   log.info(e['title'])

    # pick the best song
    if 'entries' in info:
      entry = info['entries'][0]
      #url2=info['entries'][0]["formats"][0]
    else:
      entry = info

    log.info(f"Playing {entry['title']}")
    # thumbnail description upload_date webpage_url

    # start the new song
    format = entry['formats'][0]
    stream_url = format["url"]

    source = await discord.FFmpegOpusAudio.from_probe(stream_url, **self.FFMPEG_OPTIONS)

    vc = ctx.voice_client
    vc.play(source)
    await ctx.message.remove_reaction("🤔", self.bot.user)
    await ctx.message.add_reaction("🔊")


    # announce the song
    tile = discord.Embed(
        title=entry['title'])

    tile.set_thumbnail(url=entry['thumbnail'])
    tile.url = entry['webpage_url']
    #tile.description=entry['description'])  #, color=0x00ff00)
    #tile.set_author(name=entry['uploader'], url=entry['uploader_url']) #icon_url
    #tile.timestamp = parse_date(entry['upload_date'])
    #tile.set_footer(text = info['extractor_key'])

    duration = datetime.timedelta(seconds=entry['duration'])
    upload_date = str(parse_date(entry['upload_date']).date())
    uploader = f"[{entry['uploader']}]({entry['uploader_url']})"
    tile.add_field(name="Duration", value=str(duration), inline=True)
    #tile.add_field(name="File Size", value=format['filesize'], inline=True)
    tile.add_field(name="Upload Date", value=upload_date, inline=True)
    tile.add_field(name="Uploader", value=uploader, inline=True)

    await ctx.send(embed=tile)

#desc supports [named links](https://discordapp.com)

  
  @commands.command()
  async def pause(self, ctx):
    """suspend playing of audio file, if any"""
    await ctx.voice_client.pause()

  @commands.command()
  async def resume(self, ctx):
    """continue playing suspended audio file, if any"""
    await ctx.voice_client.resume()






def setup(bot):
  bot.add_cog(MusicCog(bot))