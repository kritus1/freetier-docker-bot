#!/usr/bin/env python3
import psutil

res = str(psutil.net_io_counters(pernic=True)['eth0'][0])
f1 = open('/app/month.txt', 'w')
f2 = open('/app/eth0.txt', 'w')
f1.write(res + '\n')
f2.write(res + '\n')
f1.close()
f2.close()

import eth0
# print(eth0.reply)
