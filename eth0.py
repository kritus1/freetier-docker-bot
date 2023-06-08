#!/usr/bin/env python3
import subprocess
import psutil
from datetime import datetime

memory = psutil.virtual_memory()
disk = psutil.disk_usage('/')
boottime = datetime.fromtimestamp(psutil.boot_time())
now = datetime.now()
timedif = "Online for: %.1f Hours" % (((now - boottime).total_seconds()) / 3600)
memtotal = "Total memory: %.2f GB " % (memory.total / 1000000000)
memavail = "Available memory: %.2f GB" % (memory.available / 1000000000)
memuseperc = "Used memory: " + str(memory.percent) + " %"
diskused = "Disk used: " + str(disk.percent) + " %"
netio = psutil.net_io_counters(pernic=True)


f = open('/app/eth0.txt', 'r')
d = open('/app/delta.txt', 'r')
p = open('/app/month.txt', 'r')
fromfilestr = f.read()
foryearstr = p.read()
deltastr = d.read()
f.close()
d.close()
p.close()
if int(netio['eth0'][0]) >= int(fromfilestr):
        f = open('/app/eth0.txt', 'w')
        f.write(str(int(netio['eth0'][0]) - int(foryearstr)) + '\n')
        fromfilenew = str(int(netio['eth0'][0]) - int(foryearstr)) + '\n'
        f.close()
else:
        d = open('/app/delta.txt', 'w')
        f = open('/app/eth0.txt', 'w')
        f.write(str(int(fromfilestr) + int(netio['eth0'][0]) - int(deltastr)) + '\n')
        d.write(str(netio['eth0'][0]))
        fromfilenew = str(int(fromfilestr) + int(netio['eth0'][0]) - int(deltastr)) + '\n'
        f.close()
        d.close()

reply = timedif + "\n" + \
        memtotal + "\n" + \
        memavail + "\n" + \
        memuseperc + "\n" + \
        diskused + "\n\n" + \
        "Network I/O: " + str("%.2f" % (int(fromfilenew) / 1024 / 1024)) + " MB"
#       pidsreply + "\n\n" + \
print(reply)
