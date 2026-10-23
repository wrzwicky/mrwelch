# Music bot using youtube_dl
# basic code from TCS student and coach

# BUG Cog doesn't work! 
#  - my rpi cannot connect to voice channel
#  - "ERROR:discord.player:Probe 'native' using 'ffmpeg' failed, trying fallback" even when ffmpeg installed
#  - "site-packages/discord/player.py", line 466, in _probe_codec_native
#    IndexError: list index out of range
#    Output file #0 does not contain any stream
# TODO if you join voice channel then quit, bot uses last voice channel
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
from yt_dlp import YoutubeDL


def parse_date(s):
  y = int(s[0:4])
  m = int(s[4:6])
  d = int(s[6:8])
  return datetime.datetime(y, m, d)


class MusicCog(commands.Cog):
  """Play music from YouTube into user's voice channel."""

  def __init__(self, bot):
    self.bot = bot

    # https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py
    self.YDL_OPTIONS = {
        'format': "bestaudio[ext=m4a]/bestaudio",
        'noplaylist': True,
        'default_search': 'auto',
        'cachedir': False  #needed to avoid weird 403 errors
    }
    self.FFMPEG_OPTIONS = {
        'before_options':
        '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

  @commands.command()
  async def join(self, ctx):
    """have mrwelch join user's voice channel"""
    log.info("join()")
    if ctx.author.voice is None:
      await ctx.send("you are not in a voice channel")
      await ctx.message.add_reaction("⛔")
      return
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client:
      log.info("-moving to " + str(voice_channel))
      await ctx.voice_client.move_to(voice_channel)
    else:
      log.info("-joining " + str(voice_channel))
      await voice_channel.connect()
    log.info("-done")

  @commands.command()
  async def leave(self, ctx):
    """have mrwelch disconnect from user's voice channel"""
    if ctx.voice_client:
      await ctx.voice_client.disconnect()
    await ctx.message.add_reaction("😢")

  @commands.command()
  async def play(self, ctx, *args):
    """find suitable video on YouTube, and play the audio in user's voice channel"""
    # get arg, note progress
    song = " ".join(args)
    log.info(f"Musiccing {song}")
    await ctx.message.add_reaction("🤔")

    # ensure we're in sender's voice channel
    log.info("-call join()")
    if not ctx.voice_client:
      await self.join(ctx)
      if not ctx.voice_client or not ctx.voice_client.is_connected():
        await ctx.message.remove_reaction("🤔", self.bot.user)
        await ctx.message.add_reaction("⛔")
        await ctx.send("unable to join voice channel")
        return

    # stop current music
    log.info("-stop")
    ctx.voice_client.stop()

    # start youtube_dl
    log.info("-init DL")
    ydl = YoutubeDL(self.YDL_OPTIONS)
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

    source = await discord.FFmpegOpusAudio.from_probe(stream_url,
                                                      **self.FFMPEG_OPTIONS)

    vc = ctx.voice_client
    try:
      vc.play(source)
      await ctx.message.add_reaction("🔊")
    except Exception:
      logging.info('playback failed', exc_info=True)
      await ctx.message.add_reaction("⛔")
    finally:
      await ctx.message.remove_reaction("🤔", self.bot.user)
      
    # announce the song
    tile = discord.Embed(title=entry['title'])

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
