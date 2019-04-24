import re

import discord
import lavalink
import urllib3
from bs4 import BeautifulSoup
from redbot.core import commands

BaseCog = getattr(commands, "Cog", object)


class Lyrics(BaseCog):
    """Get Song Lyrics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def lyrics(self, ctx):
        """Search lyrics or lyrics from Mewtwo's current track."""

    pass

    @lyrics.command()
    async def search(self, ctx, *, artistsong: str):
        """
        Returns Lyrics for Song Lookup.

        User arguments - artist and song
        """

        try:
            results = lyrics_musixmatch(artistsong)
            return await ctx.send(
                '**__Lyrics for__** `' + artistsong + '`, Requested by {}'.format(ctx.message.author.mention),
                embed=discord.Embed(description=results, colour=discord.colour.Color.dark_blue()))
        except discord.HTTPException:
            return await ctx.send(
                embed=discord.Embed(description="No lyrics Found..", colour=discord.colour.Color.dark_blue()))

    @lyrics.command()
    async def playing(self, ctx):
        """
        Returns Lyrics for bot's current track.

        User arguments - artist and song
        """
        guild = ctx.guild
        aikasbaby = self.bot.get_cog('Audio')
        if aikasbaby is not None:
            try:
                player = lavalink.get_player(guild.id)
                botsong = re.compile(r"((\[)|(\()).*(of?ficial|feat\.?|ft\.?|audio|video|lyrics?|remix).*(?(2)\]|\))",
                                     flags=re.I).sub('', player.current.title).strip()
            except AttributeError:
                return await ctx.send(
                    embed=discord.Embed(description="Nothing playing.", colour=discord.colour.Color.dark_blue()))
            except KeyError:
                return await ctx.send(
                    embed=discord.Embed(description="Nothing playing.", colour=discord.colour.Color.dark_blue()))
        else:
            return await ctx.send(
                embed=discord.Embed(description="Audio not loaded.", colour=discord.colour.Color.dark_blue()))

        try:
            results = lyrics_musixmatch(botsong)
            return await ctx.send(
                '**__Lyrics for__** `' + botsong + '`' + ', Requested by {}'.format(ctx.message.author.mention),
                embed=discord.Embed(description=results, colour=discord.colour.Color.dark_blue()))
        except discord.HTTPException:
            return await ctx.send(
                embed=discord.Embed(description="No lyrics Found..", colour=discord.colour.Color.dark_blue()))


def lyrics_musixmatch(artistsong):
    artistsong = re.sub('[^a-zA-Z0-9 \n.]', '', artistsong)
    artistsong = re.sub(r'\s+', ' ', artistsong).strip()
    try:
        searchurl = "https://www.musixmatch.com/search/{}".format(artistsong).replace(" ", "%20")
        http = urllib3.PoolManager()
        searchresult = http.request('GET', searchurl)
        soup = BeautifulSoup(searchresult.data, 'html.parser')
        url = "https://www.musixmatch.com" + soup.find('a', {"class": "title"})['href']
        soup = BeautifulSoup(http.request("GET", url).data, 'html.parser')
        lyrics = soup.text.split('"body":"')[1].split('","language"')[0]
        lyrics = lyrics.replace("\\n", "\n")
        lyrics = lyrics.replace("\\", "")
        lyrics = lyrics.replace("&amp;", "&")
        lyrics = lyrics.replace("`", "'")
        lyrics = lyrics.strip()

    except Exception:
        lyrics = "No lyrics Found."

    return lyrics
