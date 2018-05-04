from sysinfo.sysinfo import psutilAvailable, SysInfo


def setup(bot):
    if psutilAvailable:
        n = SysInfo(bot)
        bot.add_cog(n)
    else:
        raise RuntimeError("You need to run 'pip3 install psutil'")