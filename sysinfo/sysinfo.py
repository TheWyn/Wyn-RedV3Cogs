from redbot.core import commands
from redbot.core import checks
import asyncio
import os
import datetime
import time
import socket
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM

BaseCog = getattr(commands, "Cog", object)

try:
    import psutil
    psutilAvailable = True
except ImportError:
    psutilAvailable = False


# Most of these scripts are from https://github.com/giampaolo/psutil/tree/master/scripts
# noinspection SpellCheckingInspection,PyPep8Naming,PyPep8Naming
class Sysinfo(BaseCog):
    """Display system information for the machine running the bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, aliases=['sys'])
    async def sysinfo(self, ctx):
        """Shows system information for the machine running the bot"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @sysinfo.command(pass_context=True)
    @checks.is_owner()
    async def info(self, ctx, *args: str):
        """Summary of cpu, memory, disk and network information
         Usage: info [option]
         Examples:
             sysinfo           Shows all available info
             sysinfo cpu       Shows CPU usage
             sysinfo memory    Shows memory usage
             sysinfo file      Shows full path of open files
             sysinfo disk      Shows disk usage
             sysinfo network   Shows network usage
             sysinfo boot      Shows boot time
         """

        options = ('cpu', 'memory', 'file', 'disk', 'network', 'boot')

        # CPU
        cpu_count_p = psutil.cpu_count(logical=False)
        cpu_count_l = psutil.cpu_count()
        if cpu_count_p is None:
            cpu_count_p = "N/A"
        cpu_cs = ("CPU Count"
                  "\n\t{0:<9}: {1:>3}".format("Physical", cpu_count_p) +
                  "\n\t{0:<9}: {1:>3}".format("Logical", cpu_count_l))
        psutil.cpu_percent(interval=None, percpu=True)
        await asyncio.sleep(1)
        cpu_p = psutil.cpu_percent(interval=None, percpu=True)
        cpu_ps = ("CPU Usage"
                  "\n\t{0:<8}: {1}".format("Per CPU", cpu_p) +
                  "\n\t{0:<8}: {1:.1f}%".format("Overall", sum(cpu_p) / len(cpu_p)))
        cpu_t = psutil.cpu_times()
        width = max([len("{:,}".format(int(n))) for n in [cpu_t.user, cpu_t.system, cpu_t.idle]])
        cpu_ts = ("CPU Times"
                  "\n\t{0:<7}: {1:>{width},}".format("User", int(cpu_t.user), width=width) +
                  "\n\t{0:<7}: {1:>{width},}".format("System", int(cpu_t.system), width=width) +
                  "\n\t{0:<7}: {1:>{width},}".format("Idle", int(cpu_t.idle), width=width))

        # Memory
        mem_v = psutil.virtual_memory()
        width = max([len(self._size(n)) for n in [mem_v.total, mem_v.available, (mem_v.total - mem_v.available)]])
        mem_vs = ("Virtual Memory"
                  "\n\t{0:<10}: {1:>{width}}".format("Total", self._size(mem_v.total), width=width) +
                  "\n\t{0:<10}: {1:>{width}}".format("Available", self._size(mem_v.available), width=width) +
                  "\n\t{0:<10}: {1:>{width}} {2}%".format("Used", self._size(mem_v.total - mem_v.available),
                                                          mem_v.percent, width=width))
        mem_s = psutil.swap_memory()
        width = max([len(self._size(n)) for n in [mem_s.total, mem_s.free, (mem_s.total - mem_s.free)]])
        mem_ss = ("Swap Memory"
                  "\n\t{0:<6}: {1:>{width}}".format("Total", self._size(mem_s.total), width=width) +
                  "\n\t{0:<6}: {1:>{width}}".format("Free", self._size(mem_s.free), width=width) +
                  "\n\t{0:<6}: {1:>{width}} {2}%".format("Used", self._size(mem_s.total - mem_s.free),
                                                         mem_s.percent, width=width))

        # Open files
        open_f = psutil.Process().open_files()
        open_fs = "Open File Handles\n\t"
        if open_f:
            if hasattr(open_f[0], "mode"):
                open_fs += "\n\t".join(["{0} [{1}]".format(f.path, f.mode) for f in open_f])
            else:
                open_fs += "\n\t".join(["{0}".format(f.path) for f in open_f])
        else:
            open_fs += "None"

        # Disk usage
        disk_u = psutil.disk_usage(os.path.sep)
        width = max([len(self._size(n)) for n in [disk_u.total, disk_u.free, disk_u.used]])
        disk_us = ("Disk Usage"
                   "\n\t{0:<6}: {1:>{width}}".format("Total", self._size(disk_u.total), width=width) +
                   "\n\t{0:<6}: {1:>{width}}".format("Free", self._size(disk_u.free), width=width) +
                   "\n\t{0:<6}: {1:>{width}} {2}%".format("Used", self._size(disk_u.used),
                                                          disk_u.percent, width=width))

        # Network
        net_io = psutil.net_io_counters()
        width = max([len(self._size(n)) for n in [net_io.bytes_sent, net_io.bytes_recv]])
        net_ios = ("Network"
                   "\n\t{0:<11}: {1:>{width}}".format("Bytes sent", self._size(net_io.bytes_sent), width=width) +
                   "\n\t{0:<11}: {1:>{width}}".format("Bytes recv", self._size(net_io.bytes_recv), width=width))

        # Boot time
        boot_s = ("Boot Time"
                  "\n\t{0}".format(datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")))

        # Output
        msg = ""
        if not args or args[0].lower() not in options:
            msg = "\n\n".join([cpu_cs, cpu_ps, cpu_ts, mem_vs, mem_ss, open_fs, disk_us, net_ios, boot_s])
        elif args[0].lower() == 'cpu':
            msg = "\n" + "\n\n".join([cpu_cs, cpu_ps, cpu_ts])
        elif args[0].lower() == 'memory':
            msg = "\n" + "\n\n".join([mem_vs, mem_ss])
        elif args[0].lower() == 'file':
            msg = "\n" + open_fs
        elif args[0].lower() == 'disk':
            msg = "\n" + disk_us
        elif args[0].lower() == 'network':
            msg = "\n" + net_ios
        elif args[0].lower() == 'boot':
            msg = "\n" + boot_s
        await ctx.send(msg)
        return

    @sysinfo.command(pass_context=True)
    @checks.is_owner()
    async def df(self, ctx):
        """File system disk space usage"""

        if len(psutil.disk_partitions(all=False)) == 0:
            await ctx.send(ctx, "psutil could not find any disk partitions")
            return

        maxlen = len(max([p.device for p in psutil.disk_partitions(all=False)], key=len))
        template = "\n{0:<{1}} {2:>9} {3:>9} {4:>9} {5:>9}% {6:>9}  {7}"
        msg = template.format("Device", maxlen, "Total", "Used", "Free", "Used ", "Type", "Mount")
        for part in psutil.disk_partitions(all=False):
            if os.name == 'nt':
                if 'cdrom' in part.opts or part.fstype == '':
                    # skip cd-rom drives with no disk in it; they may raise ENOENT,
                    # pop-up a Windows GUI error for a non-ready partition or just hang.
                    continue
            usage = psutil.disk_usage(part.mountpoint)
            msg += template.format(
                part.device,
                maxlen,
                self._size(usage.total),
                self._size(usage.used),
                self._size(usage.free),
                usage.percent,
                part.fstype,
                part.mountpoint)
        await ctx.send(msg)
        return

    @sysinfo.command(pass_context=True)
    @checks.is_owner()
    async def free(self, ctx):
        """Amount of free and used memory in the system"""

        virt = psutil.virtual_memory()
        swap = psutil.swap_memory()
        template = "\n{0:>7} {1:>9} {2:>9} {3:>9} {4:>8}% {5:>9} {6:>9} {7:>9}"
        msg = template.format("", "Total", "Used", "Free", "Used ", "Shared", "Buffers", "Cache")
        msg += template.format(
            "Memory:",
            self._size(virt.total),
            self._size(virt.used),
            self._size(virt.free),
            virt.percent,
            self._size(getattr(virt, 'shared', 0)),
            self._size(getattr(virt, 'buffers', 0)),
            self._size(getattr(virt, 'cached', 0)))
        msg += template.format(
            "Swap:",
            self._size(swap.total),
            self._size(swap.used),
            self._size(swap.free),
            swap.percent,
            "",
            "",
            "")
        await ctx.send(msg)
        return


    @sysinfo.command(pass_context=True)
    @checks.is_owner()
    async def nettop(self, ctx):
        """Snapshot of real-time network statistics"""

        # Retrieve raw stats within an interval window
        # noinspection PyUnusedLocal
        tot_before = psutil.net_io_counters()
        pnic_before = psutil.net_io_counters(pernic=True)
        await asyncio.sleep(1)
        tot_after = psutil.net_io_counters()
        pnic_after = psutil.net_io_counters(pernic=True)

        # totals
        msg = "Total Bytes:           Sent: {0:<10}   Received: {1}\n".format(
            self._size(tot_after.bytes_sent),
            self._size(tot_after.bytes_recv))
        msg += "Total Packets:         Sent: {0:<10}   Received: {1}\n".format(
            tot_after.packets_sent, tot_after.packets_recv)

        # per-network interface details: let's sort network interfaces so
        # that the ones which generated more traffic are shown first
        msg += "\n"
        nic_names = list(pnic_after.keys())
        nic_names.sort(key=lambda x: sum(pnic_after[x]), reverse=True)
        for name in nic_names:
            stats_before = pnic_before[name]
            stats_after = pnic_after[name]
            template = "{0:<15} {1:>15} {2:>15}\n"
            msg += template.format(name, "TOTAL", "PER-SEC")
            msg += "-" * 64 + "\n"
            msg += template.format(
                "bytes-sent",
                self._size(stats_after.bytes_sent),
                self._size(
                    stats_after.bytes_sent - stats_before.bytes_sent) + '/s',
            )
            msg += template.format(
                "bytes-recv",
                self._size(stats_after.bytes_recv),
                self._size(
                    stats_after.bytes_recv - stats_before.bytes_recv) + '/s',
            )
            msg += template.format(
                "pkts-sent",
                stats_after.packets_sent,
                stats_after.packets_sent - stats_before.packets_sent,
            )
            msg += template.format(
                "pkts-recv",
                stats_after.packets_recv,
                stats_after.packets_recv - stats_before.packets_recv,
            )
            msg += "\n"
        await ctx.send(msg)
        return

   
    @sysinfo.command(pass_context=True)
    @checks.is_owner()
    async def top(self, ctx):
        """Snapshot of real-time system information and tasks"""

        # sleep some time
        psutil.cpu_percent(interval=None, percpu=True)
        await asyncio.sleep(1)
        procs = []
        procs_status = {}
        for p in psutil.process_iter():
            try:
                p.dict = p.as_dict(['username', 'nice', 'memory_info',
                                    'memory_percent', 'cpu_percent',
                                    'cpu_times', 'name', 'status'])
                try:
                    procs_status[p.dict['status']] += 1
                except KeyError:
                    procs_status[p.dict['status']] = 1
            except psutil.NoSuchProcess:
                pass
            else:
                procs.append(p)

        # return processes sorted by CPU percent usage
        processes = sorted(procs, key=lambda p: p.dict['cpu_percent'],
                           reverse=True)

        # Print system-related info, above the process list
        msg = ""
        num_procs = len(procs)

        def get_dashes(perc):
            dashes = "|" * int((float(perc) / 10 * 4))
            empty_dashes = " " * (40 - len(dashes))
            return dashes, empty_dashes

        # cpu usage
        percs = psutil.cpu_percent(interval=0, percpu=True)
        for cpu_num, perc in enumerate(percs):
            dashes, empty_dashes = get_dashes(perc)
            msg += " CPU{0:<2} [{1}{2}] {3:>5}%\n".format(cpu_num, dashes, empty_dashes, perc)
        mem = psutil.virtual_memory()
        dashes, empty_dashes = get_dashes(mem.percent)
        msg += " Mem   [{0}{1}] {2:>5}% {3:>6} / {4}\n".format(
            dashes, empty_dashes,
            mem.percent,
            str(int(mem.used / 1024 / 1024)) + "M",
            str(int(mem.total / 1024 / 1024)) + "M"
        )

        # swap usage
        swap = psutil.swap_memory()
        dashes, empty_dashes = get_dashes(swap.percent)
        msg += " Swap  [{0}{1}] {2:>5}% {3:>6} / {4}\n".format(
            dashes, empty_dashes,
            swap.percent,
            str(int(swap.used / 1024 / 1024)) + "M",
            str(int(swap.total / 1024 / 1024)) + "M"
        )

        await ctx.send(msg)
        return

    @staticmethod
    def _size(num):
        for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
            if abs(num) < 1024.0:
                return "{0:.1f}{1}".format(num, unit)
            num /= 1024.0
        return "{0:.1f}{1}".format(num, "YB")

    # Respect 2000 character limit per message
    async def _say(self, ctx, msg, escape=True, wait=True):
        template = "```{0}```" if escape else "{0}"
        buf = ""
        for line in msg.splitlines():
            if len(buf) + len(line) >= 1900:
                await ctx.send(template.format(buf))
                buf = ""
                if wait:
                    await ctx.send("Type 'more' or 'm' to continue...")
                    answer = await self.bot.wait_for_message(timeout=10, author=ctx.message.author)
                    if not answer or answer.content.lower() not in ["more", "m"]:
                        await ctx.send("Command output stopped.")
                        return
            buf += line + "\n"
        if buf:
            await ctx.send(template.format(buf))


def setup(bot):
    if psutilAvailable:
        n = Sysinfo(bot)
        bot.add_cog(n)
    else:
        raise RuntimeError("You need to run 'pip3 install psutil'")
