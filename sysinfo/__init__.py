from sysinfo.sysinfo import psutilAvailable, SysInfo


def setup(bot):
    if psutilAvailable:
        n = SysInfo(bot)
        bot.add_cog(n)
    else:
        raise RuntimeError(f"You need to run '{sys.executable} -m pip install psutil'")
