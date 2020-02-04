import re
from typing import MutableMapping, Mapping

import discord
import lavalink
from bs4 import BeautifulSoup
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import pagify
from requests_futures.sessions import FuturesSession

BOT_SONG_RE = re.compile((r"((\[)|(\()).*(of?ficial|feat\.?|"
                          r"ft\.?|audio|video|lyrics?|remix|HD).*(?(2)\]|\))"), flags=re.I)


class Lyrics(commands.Cog):
    """Get Song Lyrics."""

    def __init__(self, bot):
        self.bot = bot
        self._cache: MutableMapping = {}
        self.config: Config = Config.get_conf(self, 179756535751114753, force_registration=True)
        default_guild: Mapping = dict(auto_lyrics=False)
        self.config.register_guild(**default_guild)

    def cog_unload(self):
        self._cache = {}

    @commands.Cog.listener()
    async def on_red_audio_track_start(self, guild: discord.Guild, track: lavalink.Track, requester: discord.Member):
        if not (guild and track):
            return
        if track.author.lower() not in track.title.lower():
          title = f"{track.title} - {track.author}"
        else:
          title = track.title
        self._cache[guild.id] = title
        auto_lyrics = await self.config.guild(guild).auto_lyrics()
        if auto_lyrics is True:
            notify_channel = lavalink.get_player(guild.id).fetch("channel")
            if not notify_channel:
                return
            notify_channel = self.bot.get_channel(notify_channel)
            botsong = BOT_SONG_RE.sub('', self._cache[guild.id]).strip()
            async with notify_channel.typing():
                try:
                    results = lyrics_musixmatch(botsong)
                    for page in pagify(results):
                        e = discord.Embed(title='Lyrics for __{}__'.format(botsong), description=page,
                                          colour=await self.bot.get_embed_color(notify_channel))
                        e.set_footer(text='Requested by {}'.format(track.requester))
                        await notify_channel.send(embed=e)
                except discord.Forbidden:
                    return await notify_channel.send("Missing embed permissions..")

    @commands.Cog.listener()
    async def on_red_audio_queue_end(self, guild: discord.Guild, track: lavalink.Track, requester: discord.Member):
        if not (guild and track):
            return
        if guild.id in self._cache:
            del self._cache[guild.id]

    @commands.group()
    @commands.guild_only()
    async def lyrics(self, ctx):
        """Search lyrics or lyrics from bot's current track."""

    @lyrics.command()
    async def autolyrics(self, ctx):
        """Toggle Lyrics to be shown when a new track starts"""
        auto_lyrics = await self.config.guild(ctx.guild).auto_lyrics()
        await self.config.guild(ctx.guild).auto_lyrics.set(not auto_lyrics)
        if not auto_lyrics:
            await ctx.send("Lyrics will be shown when a track starts.")
        else:
            await ctx.send("Lyrics will no longer be shown when a track starts.")

    @lyrics.command()
    async def search(self, ctx, *, artistsong: str):
        """
        Returns Lyrics for Song Lookup.
        User arguments - artist/song
        """
        async with ctx.typing():
            try:
                results = lyrics_musixmatch(artistsong)

                for page in pagify(results):
                    e = discord.Embed(title='Lyrics for __{}__'.format(artistsong), description=page,
                                      colour=await self.bot.get_embed_color(ctx.channel))
                    e.set_footer(text='Requested by {}'.format(ctx.message.author))
                    await ctx.send(embed=e)

            except discord.Forbidden:
                return await ctx.send("Missing embed permissions..")

    @lyrics.command()
    async def playing(self, ctx):
        """
        Returns Lyrics for bot's current track.
        """
        aikasbaby = self.bot.get_cog('Audio')
        if aikasbaby is not None:
            try:
                botsong = BOT_SONG_RE.sub('', self._cache[ctx.guild.id]).strip()
            except AttributeError:
                return await ctx.send("Nothing playing.")
            except KeyError:
                return await ctx.send("Nothing playing.")
        else:
            return await ctx.send("Audio not loaded.")

        async with ctx.typing():
            try:
                results = lyrics_musixmatch(botsong)
                for page in pagify(results):
                    e = discord.Embed(title='Lyrics for __{}__'.format(botsong), description=page,
                                      colour=await self.bot.get_embed_color(ctx.channel))
                    e.set_footer(text='Requested by {}'.format(ctx.message.author))
                    await ctx.send(embed=e)
            except discord.Forbidden:
                return await ctx.send("Missing embed permissions..")


def lyrics_musixmatch(artistsong):
    artistsong = re.sub('[^a-zA-Z0-9 \n.]', '', artistsong)
    artistsong = re.sub(r'\s+', ' ', artistsong).strip()
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Arch Linux; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0'}
    try:
        session = FuturesSession()
        searchresult = session.get("https://musixmatch.com/search/{}".format(artistsong).replace(" ", "%20"),
                                   headers=headers)
        soup = BeautifulSoup(searchresult.result().content, 'html.parser')
        url = "https://www.musixmatch.com" + soup.find('a', {"class": "title"})['href']
        soup = BeautifulSoup(session.get(url, headers=headers).result().content, 'html.parser')
        lyrics = soup.text.split('"body":"')[1].split('","language"')[0]
        lyrics = lyrics.replace("\\n", "\n")
        lyrics = lyrics.replace("\\", "")
        lyrics = lyrics.replace("&amp;", "&")
        lyrics = lyrics.replace("`", "'")
        lyrics = lyrics.strip()

    except Exception:
        lyrics = 'No lyrics Found.'

    return lyrics
