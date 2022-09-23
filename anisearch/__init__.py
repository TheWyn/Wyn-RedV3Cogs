from discord.utils import maybe_coroutine
from redbot.core.bot import Red

from .anisearch import AniSearch

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


async def setup(bot: Red):
    await maybe_coroutine(bot.add_cog, AniSearch(bot))
