import re

import discord
import lavalink
import requests
from bs4 import BeautifulSoup
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

BaseCog = getattr(commands, "Cog", object)
color = discord.colour.Color.dark_blue()


class Lyrics(BaseCog):
    """Get Song Lyrics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def lyrics(self, ctx):
        """Search lyrics or lyrics from bot's current track."""

    pass

    @lyrics.command()
    async def search(self, ctx, *, artistsong: str):
        """
        Returns Lyrics for Song Lookup.

        User arguments - artist/song
        """

        try:
            results = lyrics_musixmatch(artistsong)

            for page in pagify(results):
                e = discord.Embed(title='Lyrics for __{}__'.format(artistsong), description=page, colour=color)
                e.set_footer(text='Requested by {}'.format(ctx.message.author))
                await ctx.send(embed=e)

        except discord.HTTPException as e:
            return await ctx.send(embed=discord.Embed(description="{}".format(e), colour=color))

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
                return await ctx.send(embed=discord.Embed(description="Nothing playing.", colour=color))
            except KeyError:
                return await ctx.send(embed=discord.Embed(description="Nothing playing.", colour=color))
        else:
            return await ctx.send(embed=discord.Embed(description="Audio not loaded.", colour=color))

        try:
            results = lyrics_musixmatch(botsong)

            for page in pagify(results):
                e = discord.Embed(title='Lyrics for __{}__'.format(botsong), description=page, colour=color)
                e.set_footer(text='Requested by {}'.format(ctx.message.author))
                await ctx.send(embed=e)
        except discord.HTTPException:
            return await ctx.send(embed=discord.Embed(description="No lyrics Found..", colour=color))


def lyrics_musixmatch(artistsong):
    artistsong = re.sub('[^a-zA-Z0-9 \n.]', '', artistsong)
    artistsong = re.sub(r'\s+', ' ', artistsong).strip()
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Arch Linux; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0'}
    try:
        searchresult = requests.get("https://musixmatch.com/search/{}".format(artistsong).replace(" ", "%20"),
                                    headers=headers)
        soup = BeautifulSoup(searchresult.content, 'html.parser')
        url = "https://www.musixmatch.com" + soup.find('a', {"class": "title"})['href']
        soup = BeautifulSoup(requests.get(url, headers=headers).content, 'html.parser')
        lyrics = soup.text.split('"body":"')[1].split('","language"')[0]
        lyrics = lyrics.replace("\\n", "\n")
        lyrics = lyrics.replace("\\", "")
        lyrics = lyrics.replace("&amp;", "&")
        lyrics = lyrics.replace("`", "'")
        lyrics = lyrics.strip()

    except Exception:
        lyrics = 'No lyrics Found.'

    return lyrics
