import re
from typing import MutableMapping, Mapping, Optional

import discord
import lavalink
from bs4 import BeautifulSoup
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from requests_futures.sessions import FuturesSession

BOT_SONG_RE = re.compile((r"((\[)|(\()).*(of?ficial|feat\.?|"
                          r"ft\.?|audio|video|lyrics?|remix|HD).*(?(2)]|\))"), flags=re.I)


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

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_red_audio_track_start(self, guild: discord.Guild, track: lavalink.Track, requester: discord.Member):
        if not (guild and track):
            return
        if track.author.lower() not in track.title.lower():
            title = f"{track.title}"
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
            try:
                async with notify_channel.typing():
                    title, artist, lyrics, source = await getlyrics(botsong)
                    paged_embeds = []
                    paged_content = [p for p in pagify(lyrics, page_length=900)]
                    for index, page in enumerate(paged_content):
                        e = discord.Embed(title='{} by {}'.format(title, artist), description=page,
                                          colour=await self.bot.get_embed_color(notify_channel))
                        e.set_footer(
                            text='Requested by {} | Source: {} | Page: {}/{}'.format(track.requester, source, index,
                                                                                     len(paged_content)))
                        paged_embeds.append(e)
                await menu(notify_channel, paged_embeds, controls=DEFAULT_CONTROLS, timeout=180.0)
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
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def autolyrics(self, ctx):
        """Toggle Lyrics to be shown when a new track starts"""
        auto_lyrics = await self.config.guild(ctx.guild).auto_lyrics()
        await self.config.guild(ctx.guild).auto_lyrics.set(not auto_lyrics)
        if not auto_lyrics:
            await ctx.send("Lyrics will be shown when a track starts.")
        else:
            await ctx.send("Lyrics will no longer be shown when a track starts.")

    @lyrics.command()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def search(self, ctx, *, artistsong: str):
        """
        Returns Lyrics for Song Lookup.
        User arguments - artist/song
        """
        async with ctx.typing():
            title, artist, lyrics, source = await getlyrics(artistsong)
            title = "" if title == "" else '{} by {}'.format(title, artist)
            paged_embeds = []
            paged_content = [p for p in pagify(lyrics, page_length=900)]
            for index, page in enumerate(paged_content):
                e = discord.Embed(title='{}'.format(title), description=page,
                                  colour=await self.bot.get_embed_color(ctx.channel))
                e.set_footer(
                    text='Requested by {} | Source: {} | Page: {}/{}'.format(ctx.message.author, source, index,
                                                                             len(paged_content)))
                paged_embeds.append(e)
        await menu(ctx, paged_embeds, controls=DEFAULT_CONTROLS, timeout=180.0)

    @lyrics.command()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def spotify(self, ctx, user: Optional[discord.Member] = None):
        """
        Returns Lyrics from Discord Member song.
        User arguments - Mention/ID

        NOTE: This command uses Discord presence intent, enable in development portal.

        """
        if user is None:
          user = ctx.author
        spot = next((activity for activity in user.activities if isinstance(activity, discord.Spotify)), None)
        if spot is None:
            await ctx.send("{} is not listening to Spotify".format(user.name))
            return
        embed = discord.Embed(title="{}'s Spotify".format(user.name),
                              colour=await self.bot.get_embed_color(ctx.channel))
        embed.add_field(name="Song", value=spot.title)
        embed.add_field(name="Artist", value=spot.artist)
        embed.add_field(name="Album", value=spot.album)
        embed.add_field(name="Track Link",
                        value="[{}](https://open.spotify.com/track/{})".format(spot.title, spot.track_id))
        embed.set_thumbnail(url=spot.album_cover_url)
        await ctx.send(embed=embed)

        async with ctx.typing():
            title, artist, lyrics, source = await getlyrics('{} {}'.format(spot.artist, spot.title))
            title = "" if title == "" else '{} by {}'.format(title, artist)
            paged_embeds = []
            paged_content = [p for p in pagify(lyrics, page_length=900)]
            for index, page in enumerate(paged_content):
                e = discord.Embed(title='{}'.format(title), description=page,
                                  colour=await self.bot.get_embed_color(ctx.channel))
                e.set_footer(
                    text='Requested by {} | Source: {} | Page: {}/{}'.format(ctx.message.author, source, index,
                                                                             len(paged_content)))
                paged_embeds.append(e)
        await menu(ctx, paged_embeds, controls=DEFAULT_CONTROLS, timeout=180.0)

    @lyrics.command()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
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
            title, artist, lyrics, source = await getlyrics(botsong)
            title = "" if title == "" else '{} by {}'.format(title, artist)
            paged_embeds = []
            paged_content = [p for p in pagify(lyrics, page_length=900)]
            for index, page in enumerate(paged_content):
                e = discord.Embed(title='{}'.format(title), description=page,
                                  colour=await self.bot.get_embed_color(ctx.channel))
                e.set_footer(
                    text='Requested by {} | Source: {} | Page: {}/{}'.format(ctx.message.author, source, index,
                                                                             len(paged_content)))
                paged_embeds.append(e)
        await menu(ctx, paged_embeds, controls=DEFAULT_CONTROLS, timeout=180.0)


async def getlyrics(artistsong):
    percents = {" ": "+", "!": "%21", '"': "%22", "#": "%23", "$": "%24", "%": "%25", "&": "%26", "'": "%27",
                "(": "%28", ")": "%29", "*": "%2A", "+": "%2B", "`": "%60", ",": "%2C", "-": "%2D", ".": "%2E",
                "/": "%2F"}
    searchquery = ""
    for char in artistsong:
        if char in percents:
            char = percents[char]
        searchquery += char
    session = FuturesSession()
    future = session.get("https://google.com/search?q=" + searchquery + "+lyrics")
    response_one = future.result()
    soup = BeautifulSoup(response_one.text, 'html.parser')
    bouncer = "Our systems have detected unusual traffic from your computer network"
    if bouncer in soup.get_text():
        title_ = ""
        artist_ = ""
        lyrics_ = "Google has detected us being suspicious, try again later."
        source_ = ""
    else:
        try:
            title_ = soup.find('span', class_="BNeawe tAd8D AP7Wnd").get_text()
            artist_ = soup.find_all('span', class_="BNeawe s3v9rd AP7Wnd")[-1].get_text()
            lyrics_ = soup.find_all('div', class_="BNeawe tAd8D AP7Wnd")[-1].get_text()
            source_ = soup.find_all('span', class_="uEec3 AP7Wnd")[-1].get_text()
        except AttributeError:
            title_, artist_, lyrics_, source_ = "", "", "Not able to find the lyrics for {}.".format(searchquery), ""
    session.close()
    return title_, artist_, lyrics_, source_
