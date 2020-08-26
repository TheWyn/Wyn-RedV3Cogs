from sysinfo.sysinfo import psutilAvailable, SysInfo

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


def setup(bot):
    if psutilAvailable:
        n = SysInfo(bot)
        bot.add_cog(n)
    else:
        raise RuntimeError(f"You need to run '{sys.executable} -m pip install psutil'")
