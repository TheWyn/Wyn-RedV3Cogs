from .nyaa import Nyaa


def setup(bot):
    bot.add_cog(Nyaa(bot))
