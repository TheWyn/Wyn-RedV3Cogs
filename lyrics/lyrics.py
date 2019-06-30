import re

import discord
import lavalink
from bs4 import BeautifulSoup
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify
from requests_futures.sessions import FuturesSession

BaseCog = getattr(commands, "Cog", object)


class Lyrics(BaseCog):
    """Get Song Lyrics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def lyrics(self, ctx):
        """Search lyrics or lyrics from bot's current track."""

    @lyrics.command()
    async def search(self, ctx, *, artistsong: str):
        """
        Returns Lyrics for Song Lookup.

        User arguments - artist/song
        """

        try:
            results = lyrics_musixmatch(artistsong)

            for page in pagify(results):
                e = discord.Embed(title='Lyrics for __{}__'.format(artistsong), description=page,
                                  colour=await ctx.embed_color())
                e.set_footer(text='Requested by {}'.format(ctx.message.author))
                await ctx.send(embed=e)

        except discord.Forbidden:
            return await ctx.send("Missing embed permissions..")

    @lyrics.command()
    async def playing(self, ctx):
        """
        Returns Lyrics for bot's current track.

        """
        guild = ctx.guild
        aikasbaby = self.bot.get_cog('Audio')
        if aikasbaby is not None:
            try:
                player = lavalink.get_player(guild.id)
                botsong = re.compile(
                    r"((\[)|(\()).*(of?ficial|feat\.?|ft\.?|audio|video|lyrics?|remix|HD).*(?(2)\]|\))",
                    flags=re.I).sub('', player.current.title).strip()
            except AttributeError:
                return await ctx.send("Nothing playing.")
            except KeyError:
                return await ctx.send("Nothing playing.")
        else:
            return await ctx.send("Audio not loaded.")

        try:
            results = lyrics_musixmatch(botsong)

            for page in pagify(results):
                e = discord.Embed(title='Lyrics for __{}__'.format(botsong), description=page,
                                  colour=await ctx.embed_color())
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
