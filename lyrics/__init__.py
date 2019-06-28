from .lyrics import Lyrics


def setup(bot):
    bot.add_cog(Lyrics(bot))
