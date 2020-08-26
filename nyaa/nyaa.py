from bs4 import BeautifulSoup
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from requests_futures.sessions import FuturesSession

from nyaa.utils import Utils as uTils


class Nyaa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    '''
     Return a list of dicts with the results of the query.
    '''

    def search(self, keyword, **kwargs):
        category = kwargs.get('category', 0)
        subcategory = kwargs.get('subcategory', 0)
        filters = kwargs.get('filters', 0)
        page = kwargs.get('page', 0)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Arch Linux; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0'}
        session = FuturesSession()

        if page > 0:
            r = session.get(
                "http://nyaa.si/?f={}&c={}_{}&q={}&p={}&o=desc&s=seeders".format(filters, category, subcategory,
                                                                                 keyword, page), headers=headers)
        else:
            r = session.get(
                "http://nyaa.si/?f={}&c={}_{}&q={}&o=desc&s=seeders".format(filters, category, subcategory,
                                                                            keyword), headers=headers)

        soup = BeautifulSoup(r.result().text, 'html.parser')
        rows = soup.select('table tr')

        results = {}

        if rows:
            results = uTils.parse_nyaa(rows, limit=None)

        return results

    @commands.group()
    @commands.guild_only()
    async def nyaa(self, ctx):
        """Search anime."""

    @nyaa.command()
    async def lookup(self, ctx, *, text: str):
        """
        Returns torrents from search.
        User arguments - Show name
        """
        count = "5"
        pages = []
        try:
            async with ctx.typing():
                result = self.search(text)
                msg = ""
            if len(result) < int(count):
                count = len(result)
                for res in result[0:int(count):]:
                    msg += "``` Name: " + res['name'] + "\n" + \
                           "Category: " + res['category'] + "\n" + \
                           "Url: " + res['url'] + "\n" + \
                           "Torrent: " + res['download_url'] + "\n" + \
                           "Size: " + res['size'] + " --- " + \
                           "Date: " + res['date'] + " --- " + \
                           "Seeders: " + res['seeders'] + " --- " + \
                           "Leechers: " + res['leechers'] + "\n```"
                    pages.append(msg)
                    msg = ""
                await menu(ctx, pages, DEFAULT_CONTROLS)
            else:
                for res in result[0:int(count):]:
                    msg += "```Name: " + res['name'] + "\n" + \
                           "Category: " + res['category'] + "\n" + \
                           "Url: " + res['url'] + "\n" + \
                           "Torrent: " + res['download_url'] + "\n" + \
                           "Size: " + res['size'] + " --- " + \
                           "Date: " + res['date'] + " --- " + \
                           "Seeders: " + res['seeders'] + " --- " + \
                           "Leechers: " + res['leechers'] + "\n```"
                    pages.append(msg)
                    msg = ""
                await menu(ctx, pages, DEFAULT_CONTROLS)

        except Exception:
            await ctx.send(text + " not found.")
